```
SWYP-TEAM2-SERVER/
├── infra/
│   └── ansible/ 
│       ├── ansible.cfg
│       ├── inventories/
│       │   └── prod/
│       │       ├── hosts.ini
│       │       └── group_vars/
│       │           └── app.yml
│       ├── playbooks/
│       │   └── setup-app-vm.yml
│       ├── roles/
│       │   ├── common/
│       │   │   └── tasks/
│       │   │       └── main.yml
│       │   ├── docker/
│       │   │   └── tasks/
│       │   │       └── main.yml
│       │   ├── nginx/
│       │   │   ├── tasks/
│       │   │   │   └── main.yml
│       │   │   └── templates/
│       │   │       ├── app.conf.j2
│       │   │       └── app-https.conf.j2
│       │   ├── certbot/
│       │   │   ├── tasks/
│       │   │   │   └── main.yml
│       │   │   └── handlers/
│       │   │       └── main.yml
│       │   └── app/
│       │       ├── tasks/
│       │       │   └── main.yml
│       │       └── templates/
│       │           └── docker-compose.prod.yml.j2
│       └── README.md
├── Dockerfile
├── prod.env
└── requirements.txt
```
