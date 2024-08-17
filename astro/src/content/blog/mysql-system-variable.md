---
title: "[MySQL] 시스템 변수 내맘대로 설정해보기"
description: ""
pubDate: 2024-01-04
tags: ["mysql", "database"]
series: "Real MySQL 8.0 스터디"
---

Real MySQL 8.0을 읽으면서 MySQL과 데이터베이스에 대해 학습하는 [스터디](https://github.com/jaragi/real-mysql-8.0-study)를 시작했다.

책을 읽다보니 특정 기능을 활성화/비활성화하거나 특정 설정 값들을 변경하기 위해 시스템 변수를 조작하라는 내용이 많이 나온다.

예를 들어 InnoDB 버퍼풀의 크기에 대해 `innodb_buffer_pool_size` 시스템 변수를 더 큰 값으로 설정하여 버퍼 풀의 크기를 확장할 수 있다거나, `innodb_buffer_pool_instances` 시스템 변수를 이용해 버퍼 풀 인스턴스의 개수를 조절할 수 있다는 내용이다.

책에서는 MySQL 서버가 실행되는 운영체제의 리소스에 따라 시스템 변수를 적절히 조정하여 MySQL 서버의 성능을 높이는 다양한 방법들을 설명하고 있다. 이런 방법들을 적용해보기 위해서는 현재 적용되어 있는 시스템 변수를 확인하고 변경하는 방법을 확실하게 알아야겠다는 생각이 들었다.

이를 위해 로컬에 MySQL 서버를 만들어 실습하며 정리해보았다. 서버는 간단하게 mysql:latest 도커 이미지로 도커 컨테이너를 만들었다. 현 시점 8.2.0 버전이다.

MySQL 서버의 클라이언트 접속 방법(root 계정 비밀번호 접속)

```bash
docker exec -it {컨테이너 이름} mysql -u root -p
```

MySQL 서버의 파일 시스템에 데이터가 어떻게 저장되는지 조사할때는 bash 쉘을 이용해서 접속하였다.

MySQL 서버 bash 쉘 접속 방법

```bash
docker exec -it {컨테이너 이름} /bin/bash
```

## MySQL 시스템 변수

시스템 변수란? MySQL 서버 내에 저장된 변수 값들을 의미하며 메모리나 작동 방식, 접속된 사용자를 제어하기 위한 값들이다.

## 글로벌 변수와 세션 변수

MySQL의 시스템 변수는 적용 범위에 따라 글로벌 변수와 세션 변수로 나뉘는데, 일반적으로 세션별로 적용되는 시스템 변수의 경우 글로벌 변수뿐만 아니라 세션 변수에도 동시에 존재한다. 이러한 경우 [MySQL 매뉴얼](https://dev.mysql.com/doc/refman/8.0/en/server-system-variable-reference.html)의 ‘Var Scope’에는 ‘Both’라고 표시된다.

-   글로벌 변수: MySQL 서버 인스턴스 전역에 영향을 미치는 변수
-   세션 변수: MySQL 서버와 클라이언트 간의 커넥션(Session) 단위에 영향을 미치는 변수
-   Both: 세션과 글로벌 범위에 모두 적용되는 변수. 설정 파일(my.cnf 또는 my.ini)에 명시해 초기화할 수 있다. (순수하게 Session 범위의 시스템 변수는 MySQL 서버의 설정 파일에 초기값을 명시할 수 없으며, 커넥션이 만들어지는 순간부터 해당 커넥션에서만 유효하다.)

## 시스템 변수를 확인하는 명령어

SHOW 또는 SELECT 명령어를 이용해서 시스템 변수를 확인할 수 있다.

SHOW 명령어는 GLOBAL이나 SESSION키워드를 포함시켜서 글로별 변수인지 또는 세션 변수인지 명시할 수 있다.

```sql
SHOW GLOBAL VARIABLES LIKE 'var_name';
SHOW SESSION VARIABLES LIKE 'var_name';
```

GLOBAL이나 SESSION 키워드 없이 변수명으로만 검색한다면? 해당 시스템 변수가 세션 속성을 포함하면 세션 변수를 출력하고, 글로벌 속성만 가지고 있는 경우에는 글로벌 변수를 출력한다.

세션 속성만 가진 변수를 GLOBAL 키워드를 이용해서 검색할 시 오류가 발생한다.

SELECT 명령어는 다음과 같이 @@ 어노테이션을 변수명과 함께 사용할 수 있다.

```sql
SELECT @@var_name;
```

@@global.var\_name, @@session.var\_name 과 같이 global 또는 session 키워드를 붙여서 변수 종류를 명시할 수 있다. 키워드 없이 사용하면 앞서 설명과 마찬가지로 세션 속성을 포함하면 세션 변수 출력, 글로벌 속성만 있으면 글로벌 변수를 출력한다.

정리하자면, 다음과 같은 명령어들로 글로벌/세션 변수를 확인할 수 있다.

#### 전체 글로벌 변수 확인

```sql
SHOW GLOBAL VARIABLES;
```

#### 단일 글로벌 변수 확인

```sql
SHOW GLOBAL VARIABLES LIKE 'join_buffer_size';
또는
SELECT @@global.join_buffer_size;
```

#### 전체 세션 변수 확인

```sql
SHOW VARIABLES;
또는
SHOW SESSION VARIABLES;
```

#### 단일 세션 변수 확인

```sql
SHOW VARIABLES LIKE 'join_buffer_size';
또는
SELECT @@session.join_buffer_size;
또는
SELECT @@join_buffer_size;
```

#### 시스템 변수 검색 

검색 쿼리 (변수명을 정확히 모를 때는 % 와일드카드 활용)

```sql
SHOW VARIABLES LIKE 'innodb_buffer_pool%';
```

검색 결과

```
+-------------------------------------+----------------+
| Variable_name                       | Value          |
+-------------------------------------+----------------+
| innodb_buffer_pool_chunk_size       | 134217728      |
| innodb_buffer_pool_dump_at_shutdown | ON             |
| innodb_buffer_pool_dump_now         | OFF            |
| innodb_buffer_pool_dump_pct         | 25             |
| innodb_buffer_pool_filename         | ib_buffer_pool |
| innodb_buffer_pool_in_core_file     | ON             |
| innodb_buffer_pool_instances        | 1              |
| innodb_buffer_pool_load_abort       | OFF            |
| innodb_buffer_pool_load_at_startup  | ON             |
| innodb_buffer_pool_load_now         | OFF            |
| innodb_buffer_pool_size             | 134217728      |
+-------------------------------------+----------------+
11 rows in set (0.03 sec)
```

## 시스템 변수를 변경하는 명령어

시스템 변수는 MySQL 서버가 기동 중인 상태에서 변경 가능한 동적 변수와 변경 불가한 정적 변수로 나뉜다.

#### SET 명령으로 세션 변수의 autocommit 비활성화하기

MySQL에서 글로벌 변수와 세션 변수의 autocommit 값은 기본적으로 ON으로 설정되어 있다.

```
mysql> show variables like 'autocommit';
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| autocommit    | ON    |
+---------------+-------+
1 row in set (0.01 sec)

mysql> show global variables like 'autocommit';
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| autocommit    | ON    |
+---------------+-------+
1 row in set (0.01 sec)
```

SET 명령으로 세션 변수의 autocommit을 비활성화하면

```
mysql> set autocommit = OFF;
Query OK, 0 rows affected (0.01 sec)
```

세션 변수는 OFF로 변경되었고, 글로벌 변수는 그대로 ON인 것을 확인할 수 있다.

```
mysql> show variables like 'autocommit';
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| autocommit    | OFF   |
+---------------+-------+
1 row in set (0.01 sec)

mysql> show global variables like 'autocommit';
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| autocommit    | ON    |
+---------------+-------+
1 row in set (0.01 sec)
```

동적 변수를 SET GLOBAL 명령으로 변경시 MySQL 서버를 재시작할 필요 없이 즉시 반영되지만, **설정 파일에는 변경 내용이 반영되지 않아 MySQL 서버를 재시작하면 이전 값으로 돌아간다.** 이 문제를 보완하기 위해 8.0 버전에서는 SET PERSIST 명령을 도입했다.

-   SET PERSIST 명령: 설정 파일에 변경 내용 기록한다. my.cnf 파일을 수정하는 것은 아니고 별도의 파일(mysqld-auto.cnf 파일, JSON 포맷)에 기록된다.
-   SET PERSIST\_ONLY 명령: 현재 실행 중인 MySQL 서버에는 변경 내용을 적용하지 않고 다음 재시작을 위해 mysqld-auto.cnf 파일에만 변경 내용 적용한다.

## MySQL 설정 파일

설정 파일이란? MySQL 서버는 시작될 때 하나의 설정 파일을 참조하여 시스템 변수들을 초기화한다. 설정 파일의 이름은 유닉스 계열에서는 my.cnf, 윈도우 계열에서는 my.ini이다.

설정 파일을 직접 확인해보기 위해 MySQL 컨테이너에 bash 쉘로 접속해서 cat /etc/my.cnf 명령어를 이용, /etc 디렉토리에 있는 my.cnf 파일을 확인해보았다.

```
# For advice on how to change settings please see
# http://dev.mysql.com/doc/refman/8.2/en/server-configuration-defaults.html

[mysqld]
#
# Remove leading # and set to the amount of RAM for the most important data
# cache in MySQL. Start at 70% of total RAM for dedicated server, else 10%.
# innodb_buffer_pool_size = 128M
#
# Remove leading # to turn on a very important data integrity option: logging
# changes to the binary log between backups.
# log_bin
#
# Remove leading # to set options mainly useful for reporting servers.
# The server defaults are faster for transactions and fast SELECTs.
# Adjust sizes as needed, experiment to find the optimal values.
# join_buffer_size = 128M
# sort_buffer_size = 2M
# read_rnd_buffer_size = 2M

# Remove leading # to revert to previous value for default_authentication_plugin,
# this will increase compatibility with older clients. For background, see:
# https://dev.mysql.com/doc/refman/8.2/en/server-system-variables.html#sysvar_default_authentication_plugin
# default-authentication-plugin=mysql_native_password
skip-host-cache
skip-name-resolve
datadir=/var/lib/mysql
socket=/var/run/mysqld/mysqld.sock
secure-file-priv=/var/lib/mysql-files
user=mysql

pid-file=/var/run/mysqld/mysqld.pid
[client]
socket=/var/run/mysqld/mysqld.sock

!includedir /etc/mysql/conf.d/
```

설정 파일은 크게 \[mysqld\] 섹션과 \[client\] 섹션으로 나눠져 있었다. 각 섹션은 설정 그룹을 의미하며, 대체로 실행 프로그램 이름을 그룹명으로 사용한다고 한다.

\[mysqld\]의 d는 데몬(daemon, 백그라운드에서 돌아가는 프로세스)을 의미하며, \[mysqld\] 섹션의 설정 값들은 MySQL 서버 프로세스에 적용된다.

\[mysqld\] 섹션의 일부 값들을 살펴보자.

datadir=/var/lib/mysql는 서버의 데이터가 저장되는 디렉토리 경로이다. 해당 디렉토리에는 데이터 파일이 바이너리 형태로 저장되어 있다.

시험 삼아 study 데이터베이스에 member 테이블을 만들어서 레코드를 저장했을 때 다음과 같이 /var/lib/mysql/study 경로에 member.ibd 파일이 생성된 것을 확인하였고, MySQL 서버의 데이터가 디스크에 저장되는 경로를 확인할 수 있었다.

```
$ ls -lh /var/lib/mysql/study/member.ibd 
-rw-r----- 1 mysql mysql 128K Jan  2 11:31 /var/lib/mysql/study/member.ibd
```

my.cnf 파일에서 주석으로 처리된 부분 중에는 innodb_buffer_pool_size 를 설정할 수 있는 부분이 있는데, 버퍼풀의 크기를 설정할 수 있는 시스템 변수이다. MySQL에서 가장 중요한 캐시에 대한 메모리양을 설정하는 부분이라는 설명이 깨알같이 주석으로 달려있다.

```
# Remove leading # and set to the amount of RAM for the most important data
# cache in MySQL. Start at 70% of total RAM for dedicated server, else 10%.
innodb_buffer_pool_size = 128M
```

만약 설정 파일에서 innodb_buffer_pool_size = 256M으로 설정하면 MySQL 서버 실행시 버퍼 풀의 크기는 256MB로 설정된다.

```
# Remove leading # and set to the amount of RAM for the most important data # cache in MySQL. Start at 70% of total RAM for dedicated server, else 10%. innodb_buffer_pool_size = 128M
```

이렇게 설정 파일에 기록된 값을 바꾸고 MySQL 서버를 재시작하여 시스템 변수를 변경할 수도 있다.

## 마무리

이전에는 MySQL을 쓰면서 SELECT, INSERT, UPDATE, DELETE, JOIN 정도의 쿼리만 사용해보고 내부적으로 어떻게 동작하는지 잘 알지 못했는데, 시스템 변수가 어떻게 기록되고 쿼리를 통해 변경될 수 있는지 확인해보면서 MySQL 서버와 InnoDB 엔진의 전체적인 동작 방식을 이해할 수 있는 초석을 놓은 것 같다.