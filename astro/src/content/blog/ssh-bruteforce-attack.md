---
title: "SSH Bruteforce 공격 방어하기"
description: "요약: SSH 기본 포트를 변경해서 SSH Bruteforce 공격을 막아보자."
pubDate: 2023-11-26
tags: ["network", "port", "ssh"]
---

프로젝트를 배포해 놓은 NCP 서버로 SSH 브루트포스 공격이 들어오는 문제가 있었다.

## SSH Bruteforce 공격이란?

> Bruteforce는 사전의 단어 조합 또는 입력 가능한 모든 값을 무차별 대입하여 계정 정보를 획득하는 공격입니다.  
> Bruteforce가 성공할 경우 공격자가 시스템을 장악하여 정보 유출 및 악성 코드 감염 등의 2차 피해가 발생할 수 있습니다.  
> Bruteforce 공격은 다수의 공격자 IP에서 공격이 발생할 경우 공격자 IP가 표시되지 않을 수 있습니다.

SSH 로그인 실패 로그를 통해 브루트포트 공격을 확인할 수 있다.

```bash
sudo cat /var/log/auth.log | grep "sshd" | grep "Failed password"
```

실패 로그를 보면 무수히 많은 로그인 요청이 실시간으로 들어오고 있다.

![alt](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FSYRCM%2FbtsEtjtX1Hw%2Fu7tqJFEnm4NkNa9sKDMwi1%2Fimg.png)

## 해결 방안

-   매우 어려운 패스워드 생성(이미 적용)
-   root 계정 패스워드 접근 막기
-   fail2ban 아이피 차단
-   SSH 접속시 22 포트 이외의 포트 사용

### root 계정 패스워드 접근 막기

SSH 접속 후 설정 파일(sshd\_config)을 연다.

```bash
sudo vim /etc/ssh/sshd_config
```

PermitRootLogin 값을 prohibit-password 로 수정

```bash
PermitRootLogin prohibit-password
```

SSH 서비스 재시작

```bash
sudo systemctl ssh restart
```

이제 root 계정으로 올바른 패스워드를 입력해도 접근이 불가하며, private key를 이용해서만 접근 가능하다.

하지만 로그인 실패 로그에는 여전히 많은 접근이 감지된다.

수상한 IP를 차단하는건 어떨까?

### fail2ban

fail2ban은 Linux 서버를 브루트포스 공격으로부터 보호하기 위한 보안 툴이다. 로그 파일에서 반복적인 로그인 실패를 모니터링하여 해당 요청을 보내는 IP 주소를 차단한다.

#### fail2ban 설치 방법

설치 명령어

```bash
sudo apt install -y fail2ban python3-pip sqlite3 rsyslog
sudo pip3 install pyinotify
```

서비스 재시작

```bash
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban
sudo systemctl status fail2ban
```

#### fail2ban 사용 방법

SSH 접속 실패 로그 확인

```bash
sudo cat /var/log/auth.log | grep "Failed password"
```

sqlite3 데이터베이스의 bips 테이블에서 차단된 IP 조회

```bash
sudo sqlite3 /var/lib/fail2ban/fail2ban.sqlite3 "select distinct ip from bips;"
```

#### fail2ban 단축 명령어 지정

자주 사용하는 명령어들을 alias로 추가한다.

```bash
vim ~/.bashrc
```

맨 아래줄에 다음과 같이 추가한다.

```bash
alias checkban='sudo sqlite3 /var/lib/fail2ban/fail2ban.sqlite3 "select distinct ip from bips;"'
alias checkauth='sudo cat /var/log/auth.log | grep "Failed password"'
```

추가된 명령어들을 적용

```bash
source ~/.bashrc
```

alias 적용 후 터미널에서 다음 명령어를 사용할 수 있다.

```bash
checkban  # 차단된 IP 조회
checkauth # SSH 접속 실패 로그 확인
```

차단된 아이피 목록을 조회하면 다음과 같이 뜬다.

![alt](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2F22NCB%2FbtsEy5HeReB%2FO0Y9cIkljtqaLbHeaWuheK%2Fimg.png)

그런데 차단되는 IP가 점점 늘어난다… 2시간만에 이만큼 늘어남

![alt](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FbltDhk%2FbtsEysCImHw%2F8KVUyVUEEoOKpkbf7Ipv3K%2Fimg.png)

SSH 포트를 바꾸는 건 어떨까? 기본으로 설정된 22번 포트는 SSH 연결을 의미하는 [웰논 포트(Well-known port)](https://babyshark.tistory.com/18#715b3ac2-7b7e-4ed8-aad7-93d60b11aa13)이므로 수상한 공격자들은 SSH 연결이 성공할 가능성이 높은 22번 포트로 계속 연결을 시도하고 있는 것 같다.

### SSH 포트 변경하기

다시 SSH 설정 파일을 연다.

```bash
sudo vim /etc/ssh/sshd_config
```

포트를 바꿔준다.

```bash
Port 2221
```

SSH 설정을 적용하고 재실행한다.

```bash
sudo systemctl restart ssh
sudo netstat -tnlp | grep sshd
```

포트를 변경할 때는 클라우드 서비스(NCP)의 Network ACL, ACG에서도 새로운 포트의 Inbound를 열어줘야 한다. 열어주지 않으면 요청이 서버 내 포트에 접근하기 전에 서브넷과 서버 단에서 트래픽이 막혀버린다.

다음과 같이 새로운 포트로 SSH 접근할 수 있다.

```bash
ssh {사용자}@{IP 주소 또는 도메인} -p 2221
```

2221 포트로 잘 접근되는 것이 확인되면 22 포트는 SSH 설정, Network ACL, ACG에서 막아버리자.

아래와 같이 SSH 설정 파일을 수정하고, NCP 콘솔에서는 Network ACL, ACG의 Inbound 설정에서 22번 포트를 삭제한다.

```bash
# /etc/ssh/sshd_config

#Port 22
Port 2221
...
```

SSH에서 22 포트로 접근을 막은 후 22 포트로 로그인을 시도하면 연결이 거부된다.

22 포트 차단 후 10분 후 다시 Failed password 로그를 찍어보니 새로운 로그가 생기지 않았다.

![alt](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2F7M4Sd%2FbtsEy2cHcao%2FsI0hJ6YN0QWovnjcD9VOAk%2Fimg.png)
