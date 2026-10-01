from dsl import *

TRACK = "devops"

CONCEPTS = [
    C("docker.basic", 3, "Dockerfile basics",
      "A Dockerfile is a recipe for an image: start from a base, copy in your code, install dependencies, say what to run. A container is a running instance of that image.",
      [
          CODE("""
              FROM python:3.12-slim              # base image: a small Linux with Python
              WORKDIR /app                       # cd into /app (created if missing)
              COPY requirements.txt .            # copy a file from your machine into the image
              RUN pip install --no-cache-dir -r requirements.txt   # run a command at BUILD time
              COPY . .                           # now copy the rest of the code
              EXPOSE 8000                        # documentation: the app listens on 8000
              CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]   # run at START time
          """, "dockerfile"),
          TABLE(["Instruction", "When it runs", "Purpose"], [["`FROM`", "build", "choose the base image (always first)"], ["`RUN`", "build", "execute a command and keep the result in the image"], ["`COPY`", "build", "add files from your project"], ["`CMD`", "container start", "default command; can be overridden"], ["`ENTRYPOINT`", "container start", "fixed executable; arguments are appended"]]),
          UL("Build: `docker build -t reviewradar:1 .`  Run: `docker run -p 8000:8000 reviewradar:1`.", "Use the **exec form** `CMD [\"a\", \"b\"]` so signals reach your process and it stops cleanly.", "Bind servers to `0.0.0.0` inside a container. `127.0.0.1` is reachable only from inside."),
          QUICK("Which instruction runs a command while the image is being built?", ["`CMD`", "`RUN`", "`EXPOSE`", "`ENTRYPOINT`"], 1, "`RUN` executes at build time. `CMD` runs when a container starts."),
      ],
      [
          order("Put the Dockerfile lines in order for a FastAPI service.",
                "FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\"]",
                ["`FROM` is always the first instruction.", "Copy the requirements file and install before copying all the code.", "`CMD` is last."], lang="dockerfile", diff=2),
          fill("Complete the Dockerfile.", "FROM python:3.12-slim\nWORKDIR /app\n____ requirements.txt .\nRUN pip install -r requirements.txt\n____ . .\n____ [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\"]", ["COPY", "COPY", "CMD"], ["Two lines bring files into the image.", "The last line says what to run when the container starts.", "`COPY`, `COPY`, `CMD`."], lang="dockerfile", ci=True),
          mcq("What is the difference between an image and a container?", ["They are the same thing", "An image is the packaged recipe result; a container is a running instance of it", "A container is the file you build; an image is the running process", "Images exist only in the cloud"], 1,
              ["Think class and object.", "You can start many containers from one image.", "The image is read-only; the container runs."], diff=1, tags=["interview"]),
          mcq("A server inside your container binds to `127.0.0.1:8000`. From your laptop, `curl localhost:8000` (with `-p 8000:8000`) fails. Why?", ["Port 8000 is reserved", "The app only accepts connections from inside the container; it should bind to `0.0.0.0`", "Docker blocks all ports by default", "The image is too large"], 1,
              ["Where does `127.0.0.1` point inside a container?", "Published ports reach the container from outside its own loopback.", "Bind to `0.0.0.0`."], diff=3, tags=["interview"]),
      ], phases=["serving", "cloud"], minutes=5),

    C("docker.layers", 3, "Layers, caching and multi-stage builds",
      "Each instruction makes a cached layer. Order matters: put things that change rarely first, so rebuilds are fast and images stay small.",
      [
          P("Tap a line to pretend you edited it. Everything from that line downwards is rebuilt. Compare the two Dockerfiles."),
          VIZ("layers", title="Which layers rebuild?", variants=[
              {"name": "Code first (slow)", "lines": [{"ins": "FROM python:3.12-slim", "cost": 1}, {"ins": "WORKDIR /app", "cost": 1}, {"ins": "COPY . .", "cost": 1}, {"ins": "RUN pip install -r requirements.txt", "cost": 90}, {"ins": "CMD [\"python\", \"main.py\"]", "cost": 1}]},
              {"name": "Requirements first (fast)", "lines": [{"ins": "FROM python:3.12-slim", "cost": 1}, {"ins": "WORKDIR /app", "cost": 1}, {"ins": "COPY requirements.txt .", "cost": 1}, {"ins": "RUN pip install -r requirements.txt", "cost": 90}, {"ins": "COPY . .", "cost": 2}, {"ins": "CMD [\"python\", \"main.py\"]", "cost": 1}]}]),
          CODE("""
              # Multi-stage: build with the heavy tools, ship only the result
              FROM python:3.12 AS builder
              COPY requirements.txt .
              RUN pip wheel -r requirements.txt -w /wheels

              FROM python:3.12-slim
              COPY --from=builder /wheels /wheels
              RUN pip install --no-index --find-links=/wheels /wheels/*.whl
              COPY . /app
              USER nobody                          # do not run as root
              CMD ["python", "/app/main.py"]
          """, "dockerfile"),
          UL("A `.dockerignore` file (like `.gitignore`) keeps `.git`, virtual environments, caches and large data out of the build.", "Pin versions: `python:3.12-slim`, not `python:latest`, so builds are repeatable.", "Smaller images pull faster and have fewer vulnerabilities. Multi-stage builds and `-slim` bases help."),
          QUICK("You edit one Python file. In the *requirements-first* Dockerfile, which layers rebuild?", ["All of them", "Only `COPY . .` and `CMD`", "Only `FROM`", "None"], 1, "Everything above the changed line stays cached, including the slow `pip install`."),
      ],
      [
          spot("Every code change makes this build wait for `pip install` again. Which line is the problem?", "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"main.py\"]", 3,
               ["Which layer changes on every edit?", "Everything below a changed layer is rebuilt.", "Copying all the code before installing invalidates the install layer."], lang="dockerfile",
               fix=FIX("What is the fix?", ["Copy only `requirements.txt`, run `pip install`, then `COPY . .`", "Remove the `RUN` line", "Use `CMD` instead of `RUN`", "Add `--no-cache-dir`"], 0, whys=[None, "Then dependencies are never installed.", "`CMD` would try to install at container start.", "That only saves space; it does not fix the caching."]), diff=3, tags=["interview"],
               explain=EXPLAIN("In your own words: why does copying only requirements.txt first make rebuilds faster?",
                               ["Docker caches each layer and reuses it if its inputs did not change", "requirements.txt rarely changes, so the pip install layer stays cached when only code changes"],
                               "A layer is reused when its instruction and inputs are unchanged. The requirements file changes rarely, so the slow install stays cached. Code changes only invalidate the later `COPY . .` layer.")),
          fill("Complete the second stage so it uses files from the first stage.", "FROM python:3.12 AS builder\nRUN pip wheel -r requirements.txt -w /wheels\n\nFROM python:3.12-slim\nCOPY --from=____ /wheels /wheels", ["builder"], ["The first stage has a name after `AS`.", "`--from=` refers to that name.", "`builder`"], lang="dockerfile", diff=2),
          mcq("Which entries belong in `.dockerignore` for a ReviewRadar service? (Select all that apply.)", ["`.git`", "`__pycache__/`", "`requirements.txt`", "`data/raw/`"], [0, 1, 3],
              ["Ignore what the image does not need.", "The build still needs `requirements.txt`.", "History, caches and large raw data only slow the build."], diff=2),
          spot("A security scan flags this Dockerfile for an unpinned base image. Which line is the problem?", "FROM python:latest\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"main.py\"]", 1,
               ["What does `latest` mean next month?", "Builds should be repeatable.", "Pin the version."], lang="dockerfile",
               fix=FIX("What is the fix?", ["`FROM python:3.12-slim`", "`FROM python`", "`FROM python:newest`", "Delete the line"], 0), diff=2),
      ], phases=["serving", "cloud"], minutes=6),

    C("k8s.pods", 4, "Kubernetes: Deployments and Pods",
      "You tell Kubernetes the state you want (three copies of this image) and it keeps reality matching. A Deployment manages identical Pods.",
      [
          CODE("""
              apiVersion: apps/v1
              kind: Deployment
              metadata:
                name: reviewradar-api
              spec:
                replicas: 3                       # how many Pods
                selector:
                  matchLabels:
                    app: reviewradar-api          # which Pods this Deployment owns
                template:                         # the Pod blueprint
                  metadata:
                    labels:
                      app: reviewradar-api        # MUST match the selector above
                  spec:
                    containers:
                      - name: api
                        image: ghcr.io/arepaman/reviewradar:1.0
                        ports:
                          - containerPort: 8000
          """, "yaml"),
          P("Labels are how Kubernetes connects things. A Service picks Pods by label. Toggle labels below to see which Pods match."),
          VIZ("selector", title="Which pods does the Service select?", selector={"app": "web"},
              pods=[{"name": "pod-a", "labels": {"app": "web", "tier": "api"}}, {"name": "pod-b", "labels": {"app": "web", "tier": "worker"}}, {"name": "pod-c", "labels": {"app": "db", "tier": "api"}}, {"name": "pod-d", "labels": {"app": "web", "tier": "api", "env": "prod"}}]),
          UL("**Pod**: one or more containers that run together. **Deployment**: keeps N identical Pods running and handles rolling updates. **ReplicaSet** does the counting underneath.", "`kubectl apply -f deploy.yaml` sends the desired state. `kubectl get pods`, `kubectl logs <pod>`, `kubectl describe pod <pod>` show what is happening.", "If a Pod dies, the Deployment makes a new one."),
          QUICK("Which part of a Deployment must match the Pod template's labels?", ["`metadata.name`", "`spec.selector.matchLabels`", "`containerPort`", "`apiVersion`"], 1, "The selector decides which Pods the Deployment manages."),
      ],
      [
          fill("Complete the start of a Deployment.", "apiVersion: ____/v1\nkind: ____\nmetadata:\n  name: reviewradar-api\nspec:\n  replicas: 3", ["apps", "Deployment"], ["Deployments belong to the `apps` API group.", "The kind has a capital D.", "`apps` and `Deployment`."], lang="yaml", diff=2),
          spot("The Deployment applies but creates no managed Pods (the API server rejects it). Which line is the problem?", "spec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: api\n  template:\n    metadata:\n      labels:\n        app: web", 9,
               ["Compare the selector with the Pod template's labels.", "They must agree.", "`api` versus `web`."], lang="yaml",
               fix=FIX("What is the fix?", ["Make the template label `app: api` (matching the selector)", "Change `replicas` to 1", "Remove `matchLabels`", "Add `kind: Pod`"], 0), diff=3, tags=["interview"]),
          mcq("A Pod crashes. What does a Deployment with `replicas: 3` do?", ["Nothing; you must restart it", "Creates a replacement Pod to get back to 3", "Scales down to 2", "Deletes the Deployment"], 1,
              ["The Deployment holds the desired state.", "It reconciles actual state toward desired state.", "A new Pod is created."], diff=1),
      ], phases=["cloud", "serving"], minutes=5),

    C("k8s.svc", 4, "Kubernetes: Services, config, probes and resources",
      "A Service gives Pods a stable address. ConfigMaps and Secrets inject settings. Probes and resource limits keep the cluster healthy.",
      [
          CODE("""
              apiVersion: v1
              kind: Service
              metadata:
                name: reviewradar-api
              spec:
                type: ClusterIP                  # reachable inside the cluster
                selector:
                  app: reviewradar-api           # Pods with this label receive traffic
                ports:
                  - port: 80                     # the Service's port
                    targetPort: 8000             # the container's port
              ---
              # inside the container spec of the Deployment:
              resources:
                requests: {cpu: "250m", memory: "256Mi"}   # what the scheduler reserves
                limits:   {cpu: "500m", memory: "512Mi"}   # the hard ceiling
              readinessProbe:                    # only send traffic when this succeeds
                httpGet: {path: /health, port: 8000}
              livenessProbe:                     # restart the container if this keeps failing
                httpGet: {path: /health, port: 8000}
              envFrom:
                - configMapRef: {name: api-config}
                - secretRef: {name: api-secrets}
          """, "yaml"),
          UL("**Readiness** controls whether a Pod gets traffic. **Liveness** controls whether it is restarted.", "Memory units matter: `512Mi` is mebibytes, but `512` is **512 bytes**. CPU `250m` is a quarter of a core.", "A **Secret** is only base64-encoded, not encrypted. Restrict access to it and prefer an external secret store."),
          QUICK("Which probe decides whether a Pod receives traffic?", ["liveness", "readiness", "startup", "resources"], 1, "A failing readiness probe removes the Pod from the Service without restarting it."),
      ],
      [
          fill("Complete the Service so traffic on port 80 reaches the container's port 8000.", "kind: Service\nspec:\n  type: ClusterIP\n  selector:\n    app: reviewradar-api\n  ports:\n    - port: 80\n      ____: 8000", ["targetPort"], ["`port` is what the Service listens on.", "Another field names the container's port.", "`targetPort`"], lang="yaml", diff=2),
          spot("A Pod keeps being killed immediately after it starts, with `OOMKilled`. Which line is the problem?", "resources:\n  limits:\n    memory: 512\n    cpu: \"500m\"", 3,
               ["Look at the memory unit.", "A bare number means bytes.", "512 bytes is not enough for a Python process."], lang="yaml",
               fix=FIX("What is the fix?", ["`memory: 512Mi`", "`memory: \"512\"`", "`memory: 512m`", "Remove `cpu`"], 0, whys=[None, "Quotes do not change the unit; it is still bytes.", "`m` means milli, so this is half a byte.", "CPU is unrelated."]), diff=3, tags=["interview"]),
          mcq("The app takes 40 seconds to load its model. Without a readiness probe, what goes wrong?", ["Nothing", "Traffic reaches the Pod before it is ready, so requests fail", "The Pod is restarted every 5 seconds", "The Service is deleted"], 1,
              ["When does Kubernetes start sending traffic by default?", "As soon as the container is running.", "A readiness probe delays traffic until the app answers."], diff=2, tags=["interview"]),
          mcq("A Kubernetes Secret holds a database password. Which statement is true?", ["It is encrypted by default everywhere", "It is only base64-encoded, so access must be restricted", "It cannot be read by Pods", "It is public"], 1,
              ["Base64 is an encoding, not encryption.", "Anyone who can read the Secret object can decode it.", "Use RBAC and, ideally, an external secret store."], diff=2),
      ], phases=["cloud", "serving", "monitor"], minutes=6),

    C("tf.basic", 5, "Terraform: HCL basics",
      "Terraform describes infrastructure as code. You declare what should exist; Terraform works out how to get there and records what it built.",
      [
          CODE("""
              terraform {
                required_providers {
                  aws = { source = "hashicorp/aws", version = "~> 5.0" }
                }
              }

              provider "aws" {
                region = var.region
              }

              variable "region" {            # an input
                type    = string
                default = "eu-west-1"
              }

              resource "aws_s3_bucket" "models" {   # <type> <local name>
                bucket = "reviewradar-models-prod"
              }

              output "bucket_arn" {           # a value to show or share
                value = aws_s3_bucket.models.arn
              }
          """, "hcl"),
          UL("Read inputs as `var.name`, resources as `<type>.<name>.<attribute>`, locals as `local.name`.", "Workflow: `terraform init` (download providers), `terraform plan` (preview changes), `terraform apply` (make them), `terraform destroy` (remove).", "**State** (`terraform.tfstate`) maps your code to real resources. Treat it as sensitive."),
          WARN("Always read the `plan` before `apply`. A line starting with `-/+` means the resource will be destroyed and recreated."),
          QUICK("What does `terraform plan` do?", ["Creates the resources", "Shows what would change, without changing anything", "Deletes unused resources", "Formats the files"], 1, "It compares your code with the real infrastructure and previews the difference."),
      ],
      [
          fill("Complete the input variable and use it.", "____ \"region\" {\n  type    = string\n  default = \"eu-west-1\"\n}\n\nprovider \"aws\" {\n  region = ____.region\n}", ["variable", "var"], ["Inputs are declared with a block keyword.", "They are read with a short prefix.", "`variable` and `var`."], lang="hcl", diff=2),
          spot("`terraform validate` fails on this resource. Which line is the problem?", "variable \"bucket_name\" {\n  type = string\n}\nresource \"aws_s3_bucket\" \"models\" {\n  bucket = variable.bucket_name\n}", 5,
               ["How are input variables referenced?", "The block is `variable`, but the reference uses a shorter name.", "It is `var.bucket_name`."], lang="hcl",
               fix=FIX("What is the fix?", ["`bucket = var.bucket_name`", "`bucket = \"var.bucket_name\"`", "`bucket = $bucket_name`", "`bucket = input.bucket_name`"], 0), diff=2),
          mcq("`terraform plan` shows `-/+ aws_db_instance.main (must be replaced)`. What should you do before applying?", ["Apply immediately", "Check what forces the replacement; destroying a database could lose data", "Delete the state file", "Run `terraform fmt`"], 1,
              ["`-/+` means destroy then create.", "Is that acceptable for this resource?", "Investigate first, back up data if needed."], diff=3, tags=["interview"]),
      ], phases=["cloud"], minutes=6),

    C("tf.aws", 5, "Terraform on AWS: buckets, security and state",
      "A few AWS building blocks cover ReviewRadar: S3 for model files, IAM for permissions, security groups for network rules. Security mistakes here are costly.",
      [
          CODE("""
              resource "aws_s3_bucket" "models" {
                bucket = "reviewradar-models-prod"
              }

              resource "aws_s3_bucket_versioning" "models" {
                bucket = aws_s3_bucket.models.id          # reference another resource
                versioning_configuration {
                  status = "Enabled"
                }
              }

              resource "aws_security_group" "api" {
                name = "api"
                ingress {
                  from_port   = 443
                  to_port     = 443
                  protocol    = "tcp"
                  cidr_blocks = ["0.0.0.0/0"]             # HTTPS from anywhere is fine
                }
              }

              terraform {                                  # remote, locked state
                backend "s3" {
                  bucket         = "reviewradar-tfstate"
                  key            = "prod/terraform.tfstate"
                  dynamodb_table = "tf-locks"
                }
              }
          """, "hcl"),
          UL("**Least privilege**: give an IAM role only the actions and resources it needs (for example read-only access to one bucket).", "Never open SSH (22) or databases to `0.0.0.0/0`. Restrict to your office or a VPN range.", "Keep state **remote** (S3) with **locking** (DynamoDB) so two people cannot apply at once. Never commit `.tfstate` or `.tfvars` with secrets."),
          WARN("Mark secret outputs and variables `sensitive = true`, but remember state still contains them. Protect the state bucket."),
          QUICK("Which IAM policy follows least privilege for a service that only reads models?", ["`s3:*` on `*`", "`s3:GetObject` on the models bucket only", "`AdministratorAccess`", "`s3:PutObject` on all buckets"], 1, "Only the needed action, on the needed resource."),
      ],
      [
          fill("Turn on versioning for the models bucket.", "resource \"aws_s3_bucket_versioning\" \"models\" {\n  bucket = aws_s3_bucket.models.____\n  versioning_configuration {\n    status = \"____\"\n  }\n}", ["id", "Enabled"], ["Reference the bucket created above through one of its attributes.", "The status is a capitalised word.", "`id` and `Enabled`."], lang="hcl", diff=2),
          spot("A security review rejects this security group. Which line is the problem?", "resource \"aws_security_group\" \"db\" {\n  ingress {\n    from_port   = 5432\n    to_port     = 5432\n    protocol    = \"tcp\"\n    cidr_blocks = [\"0.0.0.0/0\"]\n  }\n}", 6,
               ["Who should be able to reach a database?", "`0.0.0.0/0` means the entire internet.", "Restrict it to the app's security group or a private CIDR."], lang="hcl",
               fix=FIX("What is the fix?", ["Limit the source to the app's private network (for example `10.0.0.0/16`) or its security group", "Change the port to 5433", "Change `tcp` to `udp`", "Remove `ingress`"], 0), diff=3, tags=["interview"]),
          mcq("Your team of three runs `terraform apply` from laptops. What setup avoids corrupted state?", ["Everyone keeps their own local `terraform.tfstate`", "Remote state in S3 with DynamoDB locking", "Commit `terraform.tfstate` to git", "Email the state file around"], 1,
              ["State must be shared and only one apply can run at a time.", "Local files diverge.", "A locking backend prevents simultaneous applies."], diff=2, tags=["interview"]),
      ], phases=["cloud", "monitor"], minutes=6),

    C("tf.modules", 5, "Terraform: modules, loops and data sources",
      "Modules package reusable infrastructure. `for_each` creates many similar resources, and data sources read things that already exist.",
      [
          CODE("""
              module "vpc" {                              # reuse a folder of Terraform code
                source = "./modules/vpc"
                cidr   = "10.0.0.0/16"
              }

              resource "aws_instance" "api" {
                subnet_id = module.vpc.public_subnet_id   # use a module's output
                # ...
              }

              variable "buckets" {
                default = ["models", "data", "logs"]
              }
              resource "aws_s3_bucket" "b" {
                for_each = toset(var.buckets)             # one bucket per name
                bucket   = "reviewradar-${each.key}"
              }

              data "aws_caller_identity" "me" {}          # read-only lookup of existing information
          """, "hcl"),
          UL("`count` numbers resources 0, 1, 2. **Removing one from the middle shifts the rest and can destroy resources.**", "`for_each` keys resources by name, so removing one affects only that one. Prefer it for collections.", "`terraform plan -out=tfplan` then `terraform apply tfplan` applies exactly what you reviewed.", "`lifecycle { prevent_destroy = true }` protects critical resources."),
          QUICK("You manage 3 buckets with `count` and remove the middle name from the list. What happens?", ["Only the middle bucket is destroyed", "Later buckets shift index and Terraform may destroy and recreate them", "Nothing changes", "Terraform asks which one to keep"], 1, "With `count`, resources are tracked by position."),
      ],
      [
          mcq("Why is `for_each = toset(var.names)` usually safer than `count = length(var.names)` for a list of resources?", ["It is faster to run", "Resources are tracked by name, so removing one does not shift the others", "It uses fewer API calls", "It avoids needing a provider"], 1,
              ["What identifies each resource in state?", "With `count` it is the index.", "With `for_each` it is the key."], diff=3, tags=["interview"]),
          fill("Use the module's output in another resource.", "module \"vpc\" {\n  source = \"./modules/vpc\"\n}\n\nresource \"aws_instance\" \"api\" {\n  subnet_id = module.____.public_subnet_id\n}", ["vpc"], ["The reference starts with `module.` and then the module's label.", "The label is in quotes on the first line.", "`vpc`"], lang="hcl", diff=2),
          mcq("You want to apply exactly the changes you reviewed, even if someone edits the code afterwards. What do you run?", ["`terraform apply` straight away", "`terraform plan -out=tfplan`, review, then `terraform apply tfplan`", "`terraform refresh`", "`terraform destroy`"], 1,
              ["A saved plan is a fixed set of actions.", "Apply it by file name.", "That is the reviewed-plan workflow used in CI/CD."], diff=2),
      ], phases=["cloud"], minutes=6),
]
