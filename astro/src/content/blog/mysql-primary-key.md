---
title: "[MySQL] 프라이머리 키가 일반 인덱스보다 특별한 이유"
description: "요약: MySQL 프라이머리 키는 클러스터링 인덱스이므로 B-Tree 구조의 리프 노드에 데이터가 저장되어 있다. 즉, 프라이머리 키의 B-Tree 인덱스는 한번만 탐색해도 전체 컬럼 값을 찾을 수 있다."
pubDate: 2024-01-19
tags: ["mysql", "database", "index", "primary key", "innodb"]
series: "Real MySQL 8.0 스터디"
---

프라이머리 키(PK)는 테이블에 하나밖에 없는 값이다. 오늘은 프라이머리 키가 왜 특별한지, 다른 키(인덱스)와의 차이는 무엇인지 알아보자. 참고로 이 글에서는 키(key)와 인덱스(index)를 같은 의미로 사용한다.

## InnoDB 클러스터링 인덱스

프라이머리 키의 중요성을 알기 위해서는 프라이머리 키가 클러스터링 인덱스라는 것부터 시작해야한다.

클러스터링 인덱스란 프라이머리 키 값이 비슷한 레코드끼리 묶어서 저장하는 것을 의미한다. 프라이머리 키 값에 의해 레코드의 물리적인 저장 위치가 결정되는 것이다.

MySQL에서 클러스터링 인덱스는 InnoDB 스토리지 엔진에서만 지원한다.

프라이머리 키를 기준으로 데이터가 물리적으로 정렬되어 있기 때문에 프라이머리 키 기반의 검색이 매우 빠른 장점이 있다. 대신 쓰기 작업은 느리다는 단점도 있다. 즉, 빠른 읽기(SELECT)에 장점이 있으나 느린 쓰기(INSERT, UPDATE, DELETE)에 단점이 있다.

쓰기가 느리다는 단점이 있지만, 일반적으로 웹 서비스 같은 온라인 트랜잭션 환경에서는 쓰기와 읽기 비율이 2:8, 1:9 정도이기 때문에 조금 느린 쓰기를 감수하고 읽기 속도를 빠르게 유지하는 것이 중요하다고 한다.

## 프라이머리 키(PK)와 보조 키(=세컨더리 인덱스)

프라이머리 키(Primary Key)는 레코드를 대표하는 컬럼의 값으로 만들어진다. 프라이머리 키로 설정된 컬럼은 클러스터링 인덱스로 저장되며, 자동으로 unique, not null 속성을 가진다.

보조 키(Secondary Key)는 세컨더리 인덱스(Secondary Index)라고도 하며, 프라이머리 키를 제외한 나머지 인덱스이다.

### 프라이머리 키와 세컨더리 인덱스의 핵심 차이

프라이머리 키는 클러스터링 인덱스이므로, 리프 노드에 데이터 레코드가 저장되어 있다. 즉, 프라이머리 키의 B-Tree 인덱스는 한번만 탐색해도 전체 컬럼 값을 찾을 수 있다.

[![](https://blog.kakaocdn.net/dn/bcLO5e/btsDByrVD18/ryvNn7rBguK8Lfhj139OD0/img.png)](https://blog.kakaocdn.net/dn/bcLO5e/btsDByrVD18/ryvNn7rBguK8Lfhj139OD0/img.png)

Real MySQL 8.0 1권 \[그림 8.25\]

반면 세컨더리 인덱스는 리프 노드에 프라이머리 키 값을 저장하고 있으므로, 데이터 파일을 읽기 위해선 프라이머리 키 인덱스에 대한 B-Tree를 한번 더 탐색해야한다.

[![](https://blog.kakaocdn.net/dn/b1j6OH/btsDBRefKhJ/arcQEPVV2M2QSMEM8s7kf0/img.png)](https://blog.kakaocdn.net/dn/b1j6OH/btsDBRefKhJ/arcQEPVV2M2QSMEM8s7kf0/img.png)

Real MySQL 8.0 1권 \[그림 8.6\]

세컨더리 인덱스로 검색하는 경우 다음과 같은 과정을 거친다.

-   세컨더리 인덱스 B-Tree를 탐색하여 리프 노드에 있는 프라이머리 키를 획득한다.
-   획득한 프라이머리 키를 이용해 프라이머리 키 인덱스 B-Tree를 한번 더 탐색한다.
-   프라이머리 키 인덱스의 리프 노드에 저장된 데이터 레코드를 읽는다.

## 프라이머리 키와 세컨더리 인덱스 설정 방법

프라이머리 키와 세컨더리 인덱스는 역할의 차이가 있는만큼 설정하는 방법에도 차이가 있을 것이므로, 각각 SQL로 어떻게 설정할 수 있는지 방법을 정리해보았다.

### 프라이머리 키(PK) 설정 방법

#### 테이블 생성할 때 PK 설정

```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY, -- Primary Key 설정
    ...
);
```

```sql
CREATE TABLE students (
    student_id INT,
    PRIMARY KEY (student_id)
);
```

여러개의 컬럼으로 PK를 만들 수도 있다.

```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY, -- Primary Key 설정
    first_name VARCHAR(50),
    PRIMARY KEY (student_id, first_name)
);
```

#### 테이블 생성 후 PK 설정

새로운 컬럼을 PK로 설정

```sql
ALTER TABLE table_name ADD PRIMARY KEY (column1);
```

이미 있는 컬럼을 PK로 설정

```sql
ALTER TABLE table_name MODIFY column1 datatype PRIMARY KEY;
```

### 세컨더리 인덱스 설정 방법

#### 유니크한 인덱스 생성하기

UNIQUE 제약조건을 사용해 유니크한 인덱스를 생성할 수 있다.

```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    email VARCHAR(100) UNIQUE -- UNIQUE 제약조건 설정
);
```

위와 같이 인덱스 이름을 명시하지 않으면 MySQL에서 자동으로 인덱스 이름을 생성한다.

```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY,
		email VARCHAR(100),
    UNIQUE INDEX idx_email (email) -- 인덱스 이름 명시
);
```

참고: UNIQUE 제약조건을 설정하면 해당 컬럼에 자동으로 인덱스가 생긴다. 인덱스 없이 UNIQUE 제약조건만 설정하는 방법은 없다.

#### 유니크하지 않은 인덱스 생성하기

테이블 생성할 때 인덱스 설정

```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    email VARCHAR(100) INDEX, -- INDEX 설정
);
```

```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    email VARCHAR(100),
		INDEX idx_email (email) -- 인덱스 이름 명시
);
```

테이블 생성 후 인덱스 설정

```sql
CREATE INDEX idx_email ON students(email);
```