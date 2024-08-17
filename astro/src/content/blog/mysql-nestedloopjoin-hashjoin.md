---
title: "[MySQL] 옵티마이저의 선택은? 네스티드 루프 조인 vs. 해시 조인"
description: "요약: MySQL 옵티마이저는 응답속도 면에서 우세한 네스티드 루프 조인을 주로 사용하도록 설계되어 있으며, 인덱스가 없는 등 특수한 경우에만 해시 조인을 사용한다."
pubDate: 2024-02-02
tags: ["mysql", "database", "join", "nested loop join", "hash join"]
series: "Real MySQL 8.0 스터디"
---

MySQL 데이터베이스에서 쿼리를 최적화하는 과정에서 옵티마이저는 다양한 결정을 내려야 한다. 그 중 하나는 Join과 관련한 최적화이다. 이번 시간에는 네스티드 루프 조인(Nested Loop Join)과 해시 조인(Hash Join)에 대해 살펴보고, 상황에 따라 옵티마이저가 어떤 조인 방식을 선택하는지 알아보자.

## 네스티드 루프 조인

아래와 같이 2개의 테이블을 조인하는 예시를 들어보자. member 테이블은 회원 정보를 가지고 있으며, salary 테이블은 from_date와 to_date 사이의 기간에 회원이 받은 급여 정보를 가지고 있다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FcS6D1u%2FbtsEveEyriF%2F6MCO5NfZOIkZRaXkKWjP0K%2Fimg.png)

2개의 테이블을 조인할 때 먼저 조회되는 테이블을 드라이빙 테이블(driving table), 나중에 조회되는 테이블을 드리븐 테이블(driven table)이라고 한다. 옵티마이저는 인덱스, 테이블의 크기 등을 고려하여 드라이빙 테이블을 결정한다. 일반적으로 레코드 건수가 적은 테이블이 드라이빙 테이블이 되므로 위 예시에서는 member 테이블이 드라이빙 테이블이 된다.

### 네스티드 루프 조인의 원리

네스티드 루프 조인 방식은 드라이빙 테이블(member)의 각 레코드에 대해 드리븐 테이블(salary)에서 조인 조건(member.member_id = salary.member_id)과 일치하는 레코드들을 찾는다. 이 과정이 마치 중첩된 for loop를 사용하는 것처럼 동작한다고 하여 네스티드 루프 조인이라고 한다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FbVOkpa%2FbtsEqwzee7a%2FMCt5kUvov9wlxFwKSobGj1%2Fimg.png)

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FbsV7h0%2FbtsEnTa0BKY%2F3rcVaN8YYf4DvYoFTnAne1%2Fimg.png)

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FceIN9J%2FbtsEuOMTKPH%2FMiQxbF99qKr6wede1gY9qK%2Fimg.png)

네스티드 루프 조인의 결과 다음과 같이 조인 테이블이 생성된다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FBKsB7%2FbtsEquBoJpV%2F76NFDEPkkZWymYYkXDUi4k%2Fimg.png)

### 쿼리 실행 계획

옵티마이저는 조인의 연결 조건이 되는 칼럼에 모두 인덱스가 있는 경우 네스티드 루프 조인을 사용한다.

위 예제에서는 member 테이블의 member_id, salary 테이블의 member_id 모두 인덱스가 설정되어 있어서 salary 테이블을 검색할 때 member_id에 대한 인덱스를 사용한 것이다.

EXPLAIN 명령을 사용하여 쿼리 실행 계획을 살펴보면 salary 테이블의 member_id 컬럼에 설정된 인덱스를 사용한 것을 확인할 수 있다.

```sql
EXPLAIN
SELECT *
FROM member m
	INNER JOIN salary s
		ON s.member_id = m.member_id
```

```bash
+----+-------------+-------+------------+------+---------------+---------------+---------+-------------------+------+----------+-------+
| id | select_type | table | partitions | type | possible_keys | key           | key_len | ref               | rows | filtered | Extra |
+----+-------------+-------+------------+------+---------------+---------------+---------+-------------------+------+----------+-------+
|  1 | SIMPLE      | m     | NULL       | ALL  | PRIMARY       | NULL          | NULL    | NULL              |   20 |   100.00 | NULL  |
|  1 | SIMPLE      | s     | NULL       | ref  | idx_member_id | idx_member_id | 5       | study.m.member_id |    2 |   100.00 | NULL  |
+----+-------------+-------+------------+------+---------------+---------------+---------+-------------------+------+----------+-------+
```

## 해시 조인

MySQL 8.0.18 버전부터 해시 조인이 지원되기 시작했다. 해시 조인은 테이블의 조인 조건이 되는 열을 해시 함수를 사용하여 해시 테이블에 매핑하고, 이렇게 만들어지는 해시 테이블을 기반으로 조인 작업을 수행한다. 해시 테이블은 조인 버퍼(join buffer)라고 불리는 메모리 공간에 생성된다.

### 해시 조인의 원리

해시 조인은 빌드 단계와 프로브 단계를 거친다.

#### **빌드 단계**

조인 대상 테이블 중 빌드 테이블을 선정하여 메모리에 해시 테이블을 만든다.

주로 레코드 건수가 적은 테이블이 해시 테이블을 만들기 용이하므로 빌드 테이블로 선정된다.

빌드 테이블의 조인 대상 컬럼 값을 해시하여 해시 테이블을 만든다.

#### **프로브 단계**

조인 대상 테이블 중 빌드 테이블이 아닌 다른 테이블(프로브 테이블)의 레코드를 순회하며 해시 테이블과 일치하는 레코드를 찾아 조인 테이블을 만든다.

다음은 member 테이블과 salary 테이블의 해시 조인 과정을 그림으로 표현한 것이다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FcgqJ7r%2FbtsEvwrAnhJ%2FKPHaY8zKAHVe0gwfZ5NO8k%2Fimg.png)

## 네스티드 루프 조인 vs. 해시 조인

네스티드 루프 조인과 해시 조인을 비교했을 때, 네스티드 루프 조인은 응답 속도(첫번째 레코드를 찾는데 걸리는 시간) 면에서 우세하고 해시 조인은 스루풋(throughput, 전체 레코드를 찾는데 걸리는 시간)에서 우세하다.

MySQL 서버는 주로 응답 속도가 중요한 온라인 트랜잭션(OLTP) 서비스에서 사용된다. 따라서 MySQL 옵티마이저는 주로 네스티드 루프 조인을 사용하도록 설계되어 있으며, 특수한 경우에만 해시 조인 알고리즘을 사용한다. 즉 MySQL의 해시 조인 최적화는 네스티드 루프 조인이 사용되기에 적합하지 않은 경우를 위한 차선택 같은 기능이다.

그렇다면 옵티마이저는 어떤 경우에 해시 조인을 사용할까? 조인 조건의 칼럼이 인덱스가 없거나, 조인 대상 테이블 중 일부의 레코드 건수가 매우 적은 경우 해시 조인을 사용한다.

## 쿼리 실행 계획

IGNORE INDEX를 사용해 인덱스 없이 실행하도록 한다면, 옵티마이저는 해시 조인을 사용한다. 쿼리 실행 계획을 출력해 확인해보자.

```sql
EXPLAIN
SELECT *
FROM member m IGNORE INDEX(PRIMARY, idx_first_name) 
	INNER JOIN salary s IGNORE INDEX(idx_member_id) 
		ON s.member_id = m.member_id
```

Extra 칸에 Using join buffer (hash join) 표시가 나온다.

```bash
+----+-------------+-------+------------+------+---------------+------+---------+------+------+----------+--------------------------------------------+
| id | select_type | table | partitions | type | possible_keys | key  | key_len | ref  | rows | filtered | Extra                                      |
+----+-------------+-------+------------+------+---------------+------+---------+------+------+----------+--------------------------------------------+
|  1 | SIMPLE      | m     | NULL       | ALL  | NULL          | NULL | NULL    | NULL |   20 |   100.00 | NULL                                       |
|  1 | SIMPLE      | s     | NULL       | ALL  | NULL          | NULL | NULL    | NULL |   40 |     5.00 | Using where; Using join buffer (hash join) |
+----+-------------+-------+------------+------+---------------+------+---------+------+------+----------+--------------------------------------------+
```

EXPLAIN FORMAT=TREE 또는 EXPLAIN ANALYZE 명령을 사용하면, 빌드 테이블과 프로브 테이블 구분이 쉬워진다. salary 테이블을 스캔하며 해시 테이블로 만들어진 member 테이블을 검색하는 것을 확인할 수 있다.

```bash
+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| EXPLAIN                                                                                                                                                                        |
+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| -> Inner hash join (s.member_id = m.member_id)  (cost=82.5 rows=40)
    -> Table scan on s  (cost=0.0229 rows=40)
    -> Hash
        -> Table scan on m  (cost=2.25 rows=20)
 |
+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
```