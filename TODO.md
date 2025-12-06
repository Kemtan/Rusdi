# Todo
- [x] Base bot
- [x] Utils (ping, etc)
- [x] Webhook
- [x] Github (commits, issues, and PR logger) (WIP)
  - [x] check for commit
    - [x] log every commit in specific repo
    - [x] log every commit in specific user
    - [x] check for every commit in N timespan without it getting skipped
    - [x] add cmd to store selected repo (webhook)
  - [x] check for events (currently using webhook, might remove this feature later)
    - [x] check for pull request (pull request event)
    - [x] check for branch creation (create event)
    - [x] check for starring branch (watch event)
    - [x] update to per user cmd (!events [username])
    - [ ] only display to user that ran the cmd (need to rework how the state is stored)
    - [ ] OR display into a single message:
            ```
            10 new commit
            1 starred
            1 deleted
            ```
    - [ ] AND add available arg (commit, starred, deleted) to display more info
    - [ ] Run every 3 hours
    - [x] fix events printing old events instead of latest one
  - [ ] !repo [user] cmd for listing user repo by hitting /users/{user}/repos
- [ ] reddit post sender 
- [x] implement jomok personality when tagging @Rusdi in a server via gemini api
- [ ] todo note
- [x] play music
  - [ ] support playlist to queue
- [ ] store/find doksli
- [x] run bot 24/7 in server
  - [x] setup tailscale
  - [x] setup systemd.services
- [x] setup .env.example
- [ ] setup run.sh
- [ ] clean and squash project commits