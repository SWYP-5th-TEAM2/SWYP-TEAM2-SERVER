# Mohaeng Server Ansible

Azure VM에 Mohaeng API 운영 환경을 구성하고 배포하기 위한 Ansible 프로젝트입니다.

## 구성 범위

- Ubuntu 기본 패키지 및 타임존 설정
- Docker Engine 및 Docker Compose 설치
- Azure CLI 설치
- Nginx 리버스 프록시 설정
- Certbot과 Let's Encrypt를 이용한 HTTPS 인증서 발급 및 갱신
- Azure Container Registry(ACR) 로그인
- FastAPI와 Redis 컨테이너 배포
- Alembic 데이터베이스 migration

## 디렉터리 구조

```text
infra/ansible/
├── ansible.cfg
├── requirements.yml
├── inventories/
│   └── prod/
│       ├── hosts.ini
│       └── group_vars/
│           └── app.yml
├── playbooks/
│   └── setup-app-vm.yml
└── roles/
    ├── common/
    ├── docker/
    ├── azure_cli/
    ├── nginx/
    ├── certbot/
    └── app/
```

## 사전 요구 사항

제어 호스트에 다음 프로그램이 필요합니다.

- Python 3
- Ansible Core
- SSH 클라이언트

macOS 설치 예시:

```bash
brew install ansible
```

Ansible collection을 설치합니다.

```bash
ansible-galaxy collection install \
  -r infra/ansible/requirements.yml
```

`requirements.yml`:

```yaml
---
collections:
  - name: community.docker
```

## 인벤토리

운영 서버 접속 정보는 `inventories/prod/hosts.ini`에서 관리합니다.

```ini
[app]
mohaeng-app-vm ansible_host=<VM_PUBLIC_IP>

[app:vars]
ansible_user=azureuser
ansible_ssh_private_key_file=~/.ssh/mohaeng-app-vm_key.pem
ansible_python_interpreter=/usr/bin/python3
```

SSH 개인 키, 비밀번호, 토큰은 Git에 커밋하지 않습니다.

## 운영 변수

공개 가능한 운영 설정은 `inventories/prod/group_vars/app.yml`에서 관리합니다.

```yaml
app_name: mohaeng-server
app_domain: api.mohaeng.cloud
app_dir: /opt/mohaeng-server

acr_name: mohaengacr
app_image: <ACR_LOGIN_SERVER>/mohaeng-server:release
app_port: 8000

nginx_server_name: api.mohaeng.cloud
nginx_client_max_body_size: 20M

timezone: Asia/Seoul

certbot_domain: api.mohaeng.cloud
certbot_email: <CERTBOT_EMAIL>
```

비밀번호와 애플리케이션 Secret은 이 파일에 작성하지 않습니다.

## 운영 환경변수

애플리케이션 환경변수는 VM의 다음 경로에서 직접 관리합니다.

```text
/opt/mohaeng-server/.env
```

파일 권한을 제한합니다.

```bash
sudo chown azureuser:azureuser /opt/mohaeng-server/.env
chmod 600 /opt/mohaeng-server/.env
```

Redis를 Docker 내부 네트워크에서 비밀번호 없이 사용할 경우 다음처럼 설정합니다.

```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
```

`.env` 파일은 Git과 Docker build context에 포함하면 안 됩니다.

## 연결 확인

프로젝트 루트에서 실행합니다.

```bash
ansible app \
  -i infra/ansible/inventories/prod/hosts.ini \
  -m ping
```

`infra/ansible` 디렉터리에서는 다음과 같이 실행할 수 있습니다.

```bash
ansible app -i inventories/prod/hosts.ini -m ping
```

## 문법 검사

```bash
cd infra/ansible

ansible-playbook \
  -i inventories/prod/hosts.ini \
  playbooks/setup-app-vm.yml \
  --syntax-check
```

## Playbook 실행

```bash
cd infra/ansible

ansible-playbook \
  -i inventories/prod/hosts.ini \
  playbooks/setup-app-vm.yml
```

특정 서버만 대상으로 실행하려면 `--limit`을 사용합니다.

```bash
ansible-playbook \
  -i inventories/prod/hosts.ini \
  playbooks/setup-app-vm.yml \
  --limit mohaeng-app-vm
```

## Role 역할

| Role | 역할 |
| --- | --- |
| `common` | 기본 패키지, 타임존, 앱 디렉터리 구성 |
| `docker` | Docker Engine과 Compose plugin 설치 |
| `azure_cli` | Azure CLI 저장소 등록 및 CLI 설치 |
| `nginx` | HTTP/HTTPS 리버스 프록시 구성 |
| `certbot` | Let's Encrypt 인증서 발급 및 자동 갱신 구성 |
| `app` | Compose 배포, ACR 인증, 이미지 pull, migration, 컨테이너 실행 |

## 배포 흐름

```text
Ansible 실행
→ VM Managed Identity로 Azure 로그인
→ ACR 로그인
→ release 이미지 pull
→ Alembic migration
→ FastAPI 및 Redis 실행
→ Nginx를 통해 외부 요청 전달
```

GitHub Actions CD에서는 `infra/scripts/deploy.sh`가 동일한 배포 흐름을 실행하고, Health Check 실패 시 이전 로컬 이미지로 복구합니다.

## 동작 확인

VM 컨테이너 상태:

```bash
ssh -i ~/.ssh/mohaeng-app-vm_key.pem azureuser@<VM_PUBLIC_IP>
cd /opt/mohaeng-server
docker compose ps
docker compose images
```

VM 내부 Health Check:

```bash
curl --fail http://127.0.0.1:8000/api/health
```

외부 HTTPS Health Check:

```bash
curl --fail https://api.mohaeng.cloud/api/health
```

Nginx 설정 검사:

```bash
ansible app \
  -i inventories/prod/hosts.ini \
  -b \
  -m command \
  -a "nginx -t"
```

인증서 자동 갱신 검사:

```bash
ansible app \
  -i inventories/prod/hosts.ini \
  -b \
  -m command \
  -a "certbot renew --dry-run"
```

## 로그 확인

```bash
cd /opt/mohaeng-server
docker compose logs --tail=100 fastapi
docker compose logs --tail=100 redis
sudo journalctl -u nginx --since "10 minutes ago"
```

## 보안 주의 사항

다음 파일과 값은 Git에 커밋하지 않습니다.

- `.env`, `*.env`, `prod.env`
- `*.pem`, `*.key`, SSH 개인 키
- 데이터베이스 비밀번호
- JWT 및 OAuth Secret
- Azure Client Secret

GitHub Actions는 Client Secret 대신 OIDC를 사용하고, VM은 Managed Identity로 ACR에 접근합니다.

## 현재 제한 사항

- 운영 `.env`는 VM에서 수동 관리합니다.
- 단일 FastAPI 컨테이너를 교체하므로 짧은 연결 중단이 발생할 수 있습니다.
- 이미지 롤백은 DB migration을 되돌리지 않습니다.
- Alembic migration은 이전 애플리케이션과 호환되도록 작성해야 합니다.

후속 작업으로 운영 Secret을 Ansible Vault 또는 Secret Manager로 이전하고 Blue/Green 배포를 구성합니다.
