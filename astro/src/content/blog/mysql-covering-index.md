---
title: "[MySQL] 커버링 인덱스"
description: "요약: 커버링 인덱스를 타도록 조회하면 데이터 파일을 읽지 않고 인덱스만으로 쿼리를 처리할 수 있어 조회 성능 향상에 도움된다."
pubDate: 2024-02-16
tags: ["mysql", "database", "index"]
series: "Real MySQL 8.0 스터디"
---

## 커버링 인덱스란?

데이터 파일을 전혀 읽지 않고 인덱스만으로 쿼리가 처리되는 것을 커버링 인덱스라고 한다.

first_name 칼럼에 인덱스가 설정된 employees 테이블을 예시로 살펴보자.

```bash
mysql> DESC employees;
+------------+---------------+------+-----+---------+-------+
| Field      | Type          | Null | Key | Default | Extra |
+------------+---------------+------+-----+---------+-------+
| emp_no     | int           | NO   | PRI | NULL    |       |
| birth_date | date          | NO   |     | NULL    |       |
| first_name | varchar(14)   | NO   | MUL | NULL    |       |
| last_name  | varchar(16)   | NO   |     | NULL    |       |
| gender     | enum('M','F') | NO   | MUL | NULL    |       |
| hire_date  | date          | NO   | MUL | NULL    |       |
+------------+---------------+------+-----+---------+-------+
```

약 30만건의 레코드가 있는 테이블이다.

```bash
mysql> select count(*) from employees;
+----------+
| count(*) |
+----------+
|   300024 |
+----------+
```

first_name 칼럼에 대해 인덱스 레인지 스캔(WHERE first_name BETWEEN 'Babette' AND 'Gad’)을 할 때, SELECT 대상 칼럼에 따라 실행 계획이 바뀌는 것을 확인해보자.

## SELECT * … (풀 테이블 스캔)

EXPLAIN으로 실행계획을 살펴보면 type 값이 ALL이므로 풀 테이블 스캔을 한다는 것을 알 수 있다.

```bash
mysql> explain select * from employees where first_name between 'Babette' and 'Gad';
+----+-------------+-----------+------------+------+---------------+------+---------+------+--------+----------+-------------+
| id | select_type | table     | partitions | type | possible_keys | key  | key_len | ref  | rows   | filtered | Extra       |
+----+-------------+-----------+------------+------+---------------+------+---------+------+--------+----------+-------------+
|  1 | SIMPLE      | employees | NULL       | ALL  | ix_firstname  | NULL | NULL    | NULL | 299113 |    31.36 | Using where |
+----+-------------+-----------+------------+------+---------------+------+---------+------+--------+----------+-------------+
```

실행시켜보면 0.10초 걸린다.

```bash
51169 rows in set (0.10 sec)
```

## SELECT first_name, last_name … (풀 테이블 스캔)

인덱스 레인지 스캔의 대상이 되는 인덱스(first_name)와 함께 다른 칼럼(last_name)을 조회한다.

first_name 인덱스에는 last_name 칼럼에 대한 정보가 없으므로 데이터 레코드를 조회해서 가져와야한다. 따라서 SELECT *과 마찬가지로 풀 테이블 스캔을 한다.

```bash
explain select first_name, last_name from employees where first_name between 'Babette' and 'Gad';
+----+-------------+-----------+------------+------+---------------+------+---------+------+--------+----------+-------------+
| id | select_type | table     | partitions | type | possible_keys | key  | key_len | ref  | rows   | filtered | Extra       |
+----+-------------+-----------+------------+------+---------------+------+---------+------+--------+----------+-------------+
|  1 | SIMPLE      | employees | NULL       | ALL  | ix_firstname  | NULL | NULL    | NULL | 299113 |    31.36 | Using where |
+----+-------------+-----------+------------+------+---------------+------+---------+------+--------+----------+-------------+
```

SELECT * 와 읽어들이는 레코드 수는 같지만 읽어야하는 칼럼 값이 적어 조금 빠르다.

```bash
51169 rows in set (0.07 sec)
```

## SELECT first_name … (커버링 인덱스)

인덱스 레인지 스캔의 대상이 되는 인덱스(first_name)만 조회한다.

SELECT 절에서 필요한 칼럼이 모두 인덱스에 있으므로 데이터 파일을 읽어올 필요 없이 쿼리를 처리할 수 있다. 이렇게 인덱스만으로 처리되는 것을 커버링 인덱스라고 한다.

실행계획의 type 값이 range(인덱스 레인지 스캔을 의미함)이며, Extra 칼럼에 “Using index”가 표시된다.

```bash
mysql> explain select first_name from employees where first_name between 'Babette' and 'Gad';
+----+-------------+-----------+------------+-------+---------------+--------------+---------+------+-------+----------+--------------------------+
| id | select_type | table     | partitions | type  | possible_keys | key          | key_len | ref  | rows  | filtered | Extra                    |
+----+-------------+-----------+------------+-------+---------------+--------------+---------+------+-------+----------+--------------------------+
|  1 | SIMPLE      | employees | NULL       | range | ix_firstname  | ix_firstname | 58      | NULL | 93802 |   100.00 | Using where; Using index |
+----+-------------+-----------+------------+-------+---------------+--------------+---------+------+-------+----------+--------------------------+
```

데이터 레코드를 접근하는 시간이 들지 않기 때문에 앞서 실행했던 쿼리들보다 실행시간이 짧다.

```bash
51169 rows in set (0.03 sec)
```

## SELECT first_name, emp_no … (커버링 인덱스)

인덱스 레인지 스캔의 대상이 되는 인덱스(first_name)를 프라이머리 키(emp_no)와 함께 조회한다.

여기서 중요한 점은 InnoDB 스토리지 엔진의 경우 세컨더리 인덱스에 데이터의 실제 주소 대신 프라이머리 키를 가지고 있다는 것이다. first_name과 같이 프라이머리 키가 아닌 인덱스는 인덱스 페이지 자체에 프라이머리 키를 가지고 있다. 따라서 프라이머리 키를 SELECT 대상에 넣어도 앞서 first_name만 조회한 쿼리와 비교할 때 읽어들이는 페이지의 수는 동일하다.

```bash
mysql> explain select first_name, emp_no from employees where first_name between 'Babette' and 'Gad';
+----+-------------+-----------+------------+-------+---------------+--------------+---------+------+-------+----------+--------------------------+
| id | select_type | table     | partitions | type  | possible_keys | key          | key_len | ref  | rows  | filtered | Extra                    |
+----+-------------+-----------+------------+-------+---------------+--------------+---------+------+-------+----------+--------------------------+
|  1 | SIMPLE      | employees | NULL       | range | ix_firstname  | ix_firstname | 58      | NULL | 93802 |   100.00 | Using where; Using index |
+----+-------------+-----------+------------+-------+---------------+--------------+---------+------+-------+----------+--------------------------+
```

실행시간은 first_name 칼럼만 조회할 때와 비슷하다. 인덱스만 읽느냐 아니면 데이터 페이지를 추가로 읽어야하느냐에 따라 성능이 차이나는 것을 알 수 있다.

```bash
51169 rows in set (0.03 sec)
```

## 마무리

인덱스를 읽는 것 만으로도 필요한 정보를 가져올 수 있는 경우라면 SELECT * 로 모든 칼럼을 읽어오는 것 보다 커버링 인덱스를 타도록 조회하는 것이 성능을 향상시킬 수 있다.