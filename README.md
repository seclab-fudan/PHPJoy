# PHPJoy

This document provides an overview of the directory structure and instructions for using PHPJoy.

## 1. File Description

- `./dataset`: Contains our dataset used for evaluation.
- `./PHPJoy`: Contains our proposed prototype for building the Enhanced Code Property Graph (E-CPG).
- `./api-framework`: Contains our proposed efficient security-oriented framework.
- `./tutorial`: Provides a example for quickly getting started with PHPJoy.

## 2. Usage of PHPJoy

### Environment Requirements

#### 1) Python

Version 3.9 or higher is required:

```text 
-> % python --version
Python 3.9.12
```

#### 2）PHP

Version 8.0 or higher is required:

```text 
-> % php -v
PHP 8.0.21 (cli) (built: Jul 13 2022 08:26:05) ( NTS )
Copyright (c) The PHP Group
Zend Engine v4.0.21, Copyright (c) Zend Technologies
    with Zend OPcache v8.0.21, Copyright (c), by Zend Technologies
```

#### 3) Java

Java 11 is required:

```text 
-> % java -version
openjdk version "11.0.16" 2022-07-19
OpenJDK Runtime Environment (build 11.0.16+8-post-Ubuntu-0ubuntu118.04)
OpenJDK 64-Bit Server VM (build 11.0.16+8-post-Ubuntu-0ubuntu118.04, mixed mode, sharing)
```

#### 4) Neo4j Installation

Install Neo4j with version `community-4.4.4` and move it to the project's root path.

### Graph Construction

Use composer to install:

```text 
$ cd phpjoy/php2ast/src
$ composer install
```

Parse the target project using Parser.php:

```text 
$ php ./php2ast/src/Parser.php [options] <file|folder>
```

Generate the E-CPG using phpast2cpg.jar:

```text 
$ java -jar phpast2cpg.jar  -n <nodes.csv> -e <rels.csv>
```

Import the E-CPG into Neo4j:

```text 
$ bash ./neo4j-admin-import <database_name> <bolt_ports> <http_ports>
```

Start the Neo4j service:

```text 
$ bash ../<database_name>/bin/neo4j start
```

### 3. Tutorial

We provide a simple project in `tutorial/example`

#### 1) Build the Graph Database

Generate E-CPG and import it into Neo4j:

```text 
$ cd phpjoy/
$ php ./php2ast/src/Parser.php /path/to/tutorial/example
$ java -jar phpast2cpg.jar  -n nodes.csv -e rels.csv
$ bash ./neo4j-admin-import example  17473 17474
$ ../example/bin/neo4j start
```

Note: We have prepared the generated E-CPG in `tutorial/example_cpgs`. You can copy the files from `tutorial/example_cpgs` to the `phpjoy` directory and then run `bash ./neo4j-admin-import example 17473 17474` directly.


#### 2) Configure Database Connection

Modify the `neo4j_configure_map.json` file with your Neo4j instance details:

```text 
{
  "example": {
    "NEO4J_HOST": "127.0.0.1",
    "NEO4J_PORT": 17474,
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "123",
    "NEO4J_DATABASE": "neo4j",
    "NEO4J_PROTOCOL": "http"
  }
}
```

#### 3) Run Analysis

An example analysis script is provided in `tutorial/main.py`. Execute the following commands to set up the environment and start the analysis.

```text 
uv venv
. .venv/bin/activate
uv sync
python ./main.py -1 example -vt 9 -o output
```
