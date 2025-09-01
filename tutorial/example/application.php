<?php
include "classes.php";
use BaseFramework as Framework;

Framework::init();

function dbExecute($sql){
    $db = Framework::$app;
    return $db->exec($sql);
}