<?php
class BaseFramework{
    public static DbConnection $app;
}

/**
* @property \PDO $pdo
*/
class Connection{
    public $pdo;
}

class DbConnection extends Connection{
    public function exec($sql){
        try {
            return $this->pdo->query($sql);
        } catch (PDOException $e) {
            return null;
        }
    }
}

class Fake{
    public $pdo;

    public function exec($sql){
        try {
            return $this->pdo->query($sql);
        } catch (PDOException $e) {
            return null;
        }
    }
}