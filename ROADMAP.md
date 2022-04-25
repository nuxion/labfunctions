# Roadmap

This file is used only as kind of backlog or/and draft for ideas. 

Current version: 0.7.0

## Next version 0.9.0

**MUST:**
- [ ] A default runtime available for a first time project creation
- [ ] Define if History will be written from inside the docker execution or outside
- [ ] Refactor: clean deprecated packages as core, agent and agent_client
- [ ] Security: direct implementation of a JWT System
- [ ] Security: constraint access by scopes(permissions) and claims(by project)
- [ ] Workflows: enable/disable workflows from cli
- [ ] rq_bp: Re-enable observability of jobs and workers running for admin users. 
- [ ] Tests: >= 60%
- [ ] If docker container fails, the error is not registered
- [ ] History: Save last log lines from docker container ?


**MAY:**
- [ ] E2E: complete testing of project creation, workflows push and execution
- [ ] Watch events logs on demand
- [ ] Review ExecutionTaskResult 
- [-] Timeouts default for server, tasks and clients
- [ ] Executors: Review function logic and resilience for errors. 
- [ ] Prometheus metrics
- [ ] Evaluates dockerfile generation only in server-side
- [ ] S3/GStorage plugin implementation to be used as fileserver (notebooks result, project uploads and so on)
- [ ] In WorkflowState NBTask could be a List instead of a unique value, this could allows sequencial executions of notebooks. 

**Details**

The goal of this release is keep improving stability of the system. 

The focus will be in observability and security. 

As a second goal, but maybe that's for a following release, is adding other storage options tied to google cloud an aws. 

## Next version 0.8.0

**MUST**
- [ ] NBTask args refactor 
- [ ] Does runtimes struct need a name to be associated with? 
- [x] RQWorker: Overwrite worker self ip discovery logic
- [x] RQWorker: Activity time
- [ ] RQWorker: Agent token generation for workers
- [ ] Workflows: Allows workflows execution by alias (the same for history)
- [x] Review settings strategy for server/worker
- [x] A machine types registry by cloud vendor (gcloud / digitalocean)
- [x] Autoscaling workers
- [ ] Doc: how to install client nb-workflows
- [x] Tests: >= 55%

**MAY**
- [ ] CI/CD: constraint merges to main branch
- [ ] Doc: about architecture
- [ ] Doc: branch and release strategy adopted
- [ ] Doc: User guide
- [ ] CI/CD: constraint merges to main branch
- [ ] Doc: how to install client nb-workflows
- [-] Notifications: slack and discord (*from previous release*)

**Details**
The goal of this release is adding support to autoscale machines for workers


## version 0.7.0
**MUST:**

- [x] Executios: Namespacing Execution ID for tracking loads. 
- [x] Executors: Execution ID injected from Web 
- [x] Notifications: slack and discord **keep working on this for the next release**
- [x] Tests: >= 40%
- [x] History: Execution result of a Workflow
- [x] Web: API versioning
- [x] Models: Alembic migrations implemented
- [x] Copy outputs executions locally
- [x] Project: During first time project creation review feedback if project name already exist

**MAY:**

- [x] Add project as mixin to History Model which allows to see full executions detail per project
- [x] Log execution streaming
- [x] Custom Errors
- [x] Example project using nb-workflows
- [x] Split NBClient into UserClient and AgentClient
- [x] Tracks dockerfiles versions.
- [x] Types: NBTask as pydantic model.
- [x] Types: ScheduleData as pydantic model.
- [x] Projects: File spec change where each Workflow Name will be a dict (like serivces in docker-compose.yml)
- [x] Clients refactoring: One client for command line (with filesystem side effects), Another one as agent. 
 

**Details**
The goal of this release is a functional system that delivery the promise of remote execution of notebook for production loads.
With that in mind, the focus will be in the stabilization of workflows executions, adding tests cases, execution feedback and cli enhancements.


## Draft 

**independent from a schedule release**

- [ ] Sequencial and multiple executions: option to share folders between workflows. 
- [ ] Option to convert a collab into a workflow in a project 
- [ ] Option to create a project from a notebook
- [ ] Agent which communicates only doing long-pulling to the server see [Github Actions Runner](https://github.com/actions/runner) 
- [ ] Refresh Token: rotates whit each refresh request (idea: tracks refresh token with access_token..)
- [ ] Review private_key strategy, evaluate [sealed boxes](https://libsodium.gitbook.io/doc/public-key_cryptography/sealed_boxes) 
- [ ] Allows Control plane to spawn machines
- [ ] If a job dies by timeout or by a runtime error, the docker spawned will still be running, review this case. 
- [ ] Default project for each user ? this will allow uploading and executing notebooks from any place without worryng about dependencies. 
- [ ] Separation between client and server, settings flag ? base settings shared? 
- [ ] Jupyter on demand instance
- [ ] Executors: Docker volumes specification **cancelled**
- [ ] Optional [Any] Dockerfile RUN command definition from settings. **Cancelled**
- [x] Executors: SeqPipe implmentation **cancelled**
