# Roadmap

This file is used only as kind of backlog or/and draft for ideas. 

## Next version 0.7.0

**MUST:**

- [x] Executors: SeqPipe implmentation [deprecated]
- [- ] Executors: Docker volumes specification
- [x] Executios: Namespacing Execution ID for tracking loads. 
- [x] Executors: Execution ID injected from Web 
- [-] Notifications: slack and discord
- [ ] Doc: about architecture
- [ ] Doc: how to install client nb-workflows
- [ ] Doc: branch and release strategy adopted
- [x] Tests: >= 40%
- [x] History: Execution result of a Workflow
- [ ] Web: API versioning
- [ ] Models: Alembic migrations implemented
- [-] Copy outputs executions locally

**MAY:**

- [x] Log execution streaming
- [ ] Jupyter on demand instance [x]
- [-] Custom Errors
- [ ] Example project using nb-workflows
- [ ] Timeouts default for server, tasks and clients
- [x] Split NBClient into UserClient and AgentClient
- [ ] CI/CD: constraint merges to main branch
- [ ] Optional [Any] Dockerfile RUN command definition from settings.
- [-] Tracks dockerfiles versions.
- [x] Types: NBTask as pydantic model.
- [x] Types: ScheduleData as pydantic model.
- [x] Projects: File spec change where each Workflow Name will be a dict (like serivces in docker-compose.yml)
- [x] Clients refactoring: One client for command line (with filesystem side effects), Another one as agent. 
 

**Details**

SeqPipe: The idea is the definition of simple execution pipelines where a pipeline will execute an array of workflows *exact in order*. 
Because they are execution in order, could be executed in the same machine and could share volumes data. 

Two possible implementations could exist for this:
And standarized `cache` folder from where to build shared resources between workflows or,
let the user define the folrders shared between workflows


## Draft

- [ ] Option to convert a collab into a workflow in a project 
- [ ] Option to create a project from a notebook
- [ ] Agent which communicates only doing long-pulling to the server see [Github Actions Runner](https://github.com/actions/runner) 
- [ ] DagPipe: A pipeline which allows running workflows in parallel.
- [ ] Refresh Token: rotates whit each refresh request (idea: tracks refresh token with access_token..)
- [ ] Review private_key strategy, evaluate [sealed boxes](https://libsodium.gitbook.io/doc/public-key_cryptography/sealed_boxes) 
- [ ] Allows Control plane to spawn machines
- [ ] If a job dies by timeout or by a runtime error, the docker spawned will still be running, review this case. 
- [ ] Default project for each user ? this will allow uploading and executing notebooks from any place without worryng about dependencies. 
- [ ] Separation between client and server, settings flag ? base settings shared? 
 

