from dsl import *

TRACK = "devops"

CONCEPTS = [
    C("k8s.scale", 4, "Kubernetes: scaling, rollouts and debugging",
      "Production Kubernetes is mostly three questions: how many Pods, how do updates roll out, and why is this Pod unhappy?",
      [
          CODE("""
              apiVersion: autoscaling/v2
              kind: HorizontalPodAutoscaler
              metadata:
                name: reviewradar-api
              spec:
                scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: reviewradar-api}
                minReplicas: 2
                maxReplicas: 10
                metrics:
                  - type: Resource
                    resource:
                      name: cpu
                      target: {type: Utilization, averageUtilization: 70}   # scale out above 70% of the CPU request

              # in the Deployment:
              strategy:
                type: RollingUpdate
                rollingUpdate:
                  maxSurge: 1            # one extra Pod during the update
                  maxUnavailable: 0      # never drop below the desired count
          """, "yaml"),
          TABLE(["Status you see", "Usual cause", "First command"], [["`CrashLoopBackOff`", "the container starts and exits", "`kubectl logs POD --previous`"], ["`ImagePullBackOff`", "wrong image name or tag, or no registry credentials", "`kubectl describe pod POD` (Events)"], ["`Pending`", "no node has enough CPU or memory", "`kubectl describe pod POD`"], ["`OOMKilled`", "memory limit too low", "check `resources.limits.memory`"]]),
          UL("`kubectl rollout status deploy/NAME` follows an update. `kubectl rollout undo deploy/NAME` goes back one version.", "The autoscaler needs CPU/memory **requests** set (it measures use as a percentage of the request) and a metrics server in the cluster.", "A **readiness probe** is what makes rolling updates safe: new Pods only receive traffic once they pass it."),
          QUICK("A Pod is in `CrashLoopBackOff`. What do you check first?", ["The Service selector", "The previous container's logs: `kubectl logs POD --previous`", "The node's disk", "The Ingress"], 1, "The container keeps dying. Its last words are in the previous logs."),
      ],
      [
          fill("Scale between 2 and 10 Pods, targeting 70% CPU utilisation.", "spec:\n  minReplicas: 2\n  maxReplicas: ____\n  metrics:\n    - type: Resource\n      resource:\n        name: cpu\n        target:\n          type: Utilization\n          averageUtilization: ____", [["10"], ["70"]], ["The ceiling for the number of Pods.", "The target is a percentage of the CPU request.", "`10` and `70`."], lang="yaml", diff=2),
          spot("During every release the API has a short outage. Which line is the problem?", "strategy:\n  type: RollingUpdate\n  rollingUpdate:\n    maxSurge: 1\n    maxUnavailable: 100%", 5,
               ["How many old Pods may be taken down at once?", "100% means all of them.", "New Pods are not ready yet."], lang="yaml",
               fix=FIX("What is the fix?", ["Set `maxUnavailable: 0` (or a small number) so ready Pods always remain", "Set `maxSurge: 0`", "Change `type` to `Recreate`", "Add more replicas and keep 100%"], 0, whys=[None, "With `maxSurge: 0` and some unavailable allowed the update still dips, and with 0 and 0 it cannot progress.", "`Recreate` kills everything first, which is the outage.", "More replicas do not help if all are taken down at once."]), diff=3, tags=["interview"]),
          mcq("The autoscaler shows `<unknown>/70%` for CPU and never scales. What is the most likely cause?", ["The Service has no selector", "The Pods have no CPU request (or the metrics server is missing)", "The image is too large", "The replicas are set to 1"], 1,
              ["Utilisation is measured against the request.", "No request means no percentage.", "The metrics server provides the numbers."], diff=3, tags=["interview"]),
          mcq("A new version is broken, and users are seeing errors. What is the fastest safe way back?", ["Edit the Pod by hand", "`kubectl rollout undo deployment/reviewradar-api`", "Delete the namespace", "Scale to zero and wait"], 1,
              ["The Deployment remembers its earlier revisions.", "One command returns to the previous one.", "Investigate the cause afterwards."], diff=2),
      ], phases=["cloud", "serving"], minutes=6),

    C("gha.deploy", 5, "CI/CD: build, push and deploy to AWS",
      "A good pipeline builds one image per commit, pushes it to a registry and deploys it, without any long-lived password sitting in GitHub.",
      [
          CODE("""
              name: deploy
              on:
                push:
                  branches: [main]
              permissions:
                id-token: write            # lets the job ask GitHub for a short-lived identity token (OIDC)
                contents: read
              concurrency:
                group: deploy-prod
                cancel-in-progress: false  # never kill a deploy that is already running
              jobs:
                deploy:
                  runs-on: ubuntu-latest
                  environment: production  # can require a human approval
                  steps:
                    - uses: actions/checkout@v4
                    - uses: aws-actions/configure-aws-credentials@v4
                      with:
                        role-to-assume: arn:aws:iam::123456789012:role/github-deploy
                        aws-region: eu-west-1
                    - uses: aws-actions/amazon-ecr-login@v2
                    - run: docker build -t $REGISTRY/reviewradar:${{ github.sha }} .
                    - run: docker push $REGISTRY/reviewradar:${{ github.sha }}
                    - run: kubectl set image deployment/reviewradar-api api=$REGISTRY/reviewradar:${{ github.sha }}
          """, "yaml"),
          UL("**OIDC**: AWS trusts GitHub's short-lived token for one role. There is no `AWS_SECRET_ACCESS_KEY` to leak or rotate.", "Tag images with the **commit SHA** (`github.sha`), not `latest`. Every deploy is traceable, and rollback means redeploying an old SHA.", "`environment: production` can demand a reviewer's approval. `concurrency` stops two deploys racing.", "Run tests in an earlier job and use `needs: test` so a red build never deploys."),
          WARN("Long-lived cloud keys stored as repository secrets are a top cause of breaches. Prefer a role the workflow assumes through OIDC, limited to exactly what it needs."),
          QUICK("Why tag images with the commit SHA instead of `latest`?", ["It is shorter", "You know exactly what is running and can roll back to an exact earlier build", "Docker requires it", "It makes builds faster"], 1, "`latest` moves, so it tells you nothing about what is deployed."),
      ],
      [
          spot("A security review rejects this step. Which line is the problem?", "- uses: aws-actions/configure-aws-credentials@v4\n  with:\n    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}\n    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}", 3,
               ["What kind of credentials are these?", "They never expire unless someone rotates them.", "A role assumed through OIDC has no stored secret at all."], lang="yaml",
               fix=FIX("What is the better approach?", ["Use `role-to-assume` with OIDC and `permissions: id-token: write`", "Rename the secrets", "Store the keys in the repository README", "Share one key across all projects"], 0), diff=3, tags=["interview"]),
          fill("Tag the image with the commit and allow OIDC.", "permissions:\n  id-token: ____\n...\n- run: docker build -t $REGISTRY/reviewradar:${{ github.____ }} .", [["write"], ["sha"]], ["The job needs permission to write an identity token.", "GitHub exposes the commit hash in the `github` context.", "`write` and `sha`."], lang="yaml", diff=2),
          order("Put the steps of the deploy job in order.", "- uses: actions/checkout@v4\n- uses: aws-actions/configure-aws-credentials@v4\n- uses: aws-actions/amazon-ecr-login@v2\n- run: docker build -t app:${{ github.sha }} .\n- run: docker push app:${{ github.sha }}",
                ["Code first, then credentials.", "You must log in to the registry before pushing.", "Build before push."], lang="yaml", diff=2),
          mcq("What does `concurrency: {group: deploy-prod, cancel-in-progress: false}` do?", ["Runs deploys in parallel", "Queues deploys so only one runs at a time, and never cancels a running one", "Cancels the older run when a new commit arrives", "Limits CPU usage"], 1,
              ["Same group means same queue.", "`cancel-in-progress: false` protects the running deploy.", "Two simultaneous deploys could leave the cluster half updated."], diff=3, tags=["interview"]),
      ], phases=["cloud", "serving"], minutes=7),

    C("tf.state", 5, "Terraform state, drift and import",
      "The state file is Terraform's memory. Most real-world Terraform trouble is about state: drift, shared access and adopting resources that already exist.",
      [
          CODE("""
              terraform plan                              # compares code, state and the real cloud
              terraform plan -refresh-only                # only report drift (changes made outside Terraform)
              terraform import aws_s3_bucket.models my-existing-bucket    # adopt an existing resource into state
              terraform state list                        # what does Terraform manage?
              terraform state rm aws_s3_bucket.old        # stop managing it (does not delete it)
          """, "bash"),
          UL("**Drift**: someone changed a resource in the console. The next `plan` will try to revert it to match the code.", "**Import** attaches an existing resource to a block in your code so Terraform manages it. Write the block first, then import.", "Use one remote state per environment (dev, prod) so a mistake in dev cannot touch prod. Folders or separate backends are safer than workspaces for strongly separated environments.", "Never edit the state file by hand. Use `terraform state` commands."),
          WARN("`terraform state rm` and `import` do not change the real infrastructure, only what Terraform believes. A wrong move can later lead Terraform to create a duplicate or destroy something."),
          QUICK("A teammate changed a security group in the AWS console. What will the next `terraform plan` show?", ["Nothing", "A change that puts the security group back as your code defines it", "An error", "The new console settings added to your code"], 1, "Terraform treats your code as the truth and plans to undo the drift."),
      ],
      [
          mcq("Someone edited a bucket's tags in the AWS console. You want to know what changed outside Terraform, without proposing to change anything. Which command fits?", ["`terraform apply`", "`terraform plan -refresh-only`", "`terraform destroy`", "`terraform fmt`"], 1,
              ["You only want to see drift.", "A flag restricts the plan to refreshing state.", "`-refresh-only`."], diff=3, tags=["interview"]),
          fill("Bring an existing bucket under Terraform's management.", "terraform ____ aws_s3_bucket.models my-existing-bucket", [["import"]], ["The resource already exists in AWS.", "You need to attach it to a block in your state.", "`import`"], lang="bash", diff=2),
          spot("This sequence is risky. Which line is the problem?", "git add main.tf\ngit add terraform.tfstate\ngit commit -m \"infra\"", 2,
               ["What does the state file contain?", "It can hold passwords and keys in plain text.", "It should live in remote, locked storage, never in git."], lang="bash",
               fix=FIX("What is the fix?", ["Keep state in a remote backend (S3 with locking) and add `*.tfstate*` to `.gitignore`", "Commit it, but in a private repository", "Encrypt the file with a simple zip password", "Rename it to `state.txt`"], 0), diff=3, tags=["interview"]),
          mcq("You have `dev` and `prod`. Which layout best prevents a mistake in dev from touching prod?", ["One state, one folder, and a variable for the environment", "Separate state files (own backend key or folder) per environment, ideally with different credentials", "Terraform workspaces with the same credentials for everything", "Run everything from a laptop"], 1,
              ["Isolation limits the blast radius.", "Different state means different resources.", "Different credentials mean dev code cannot even reach prod."], diff=3, tags=["interview"]),
      ], phases=["cloud"], minutes=6),
]
