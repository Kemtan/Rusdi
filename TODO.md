# Todo
- [x] Base bot
- [x] Utils (ping, etc)
- [ ] Github (commits, issues, and PR logger) (WIP)
  - [ ] check for commit
    - [x] log every commit in specific repo
    - [ ] log every commit in specific user
    - [ ] check for every commit in N timespan without it getting skipped
    - [ ] add cmd to store selected repo
    - [ ] automaticly select latest changes in the repo
  - [x] check for events
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
  - [ ] !repo [user] cmd for listing user repo by hitting /users/{user}/repos
- [ ] reddit post sender 
- [ ] implement jomok personality when tagging @Rusdi in a server via gemini api
- [ ] todo note
- [ ] play music
- [ ] store/find doksli
- [x] run bot 24/7 in server
  - [x] setup tailscale
  - [x] setup systemd.services
- [x] setup .env.example
- [ ] clean and squash project commits