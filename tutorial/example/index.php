<?php
define("APP","application");
const U_TOKEN = "user_token";
const IS_DRAFT = "is_draft";
include dirname(__FILE__).DIRECTORY_SEPARATOR.APP.".php";
$info = array("detail"=>$_POST["details"]);
$info[IS_DRAFT] = true;
$info[U_TOKEN] = $_POST["token"];
$sid = intval($info["detail"]["sid"]);
$sql = "SELECT usesleft FROM t_{$sid}";
$sql .=" WHERE t='".$info[U_TOKEN]. "'";
$result = dbExecute($sql);
if ($result) {
    $row = $result->fetch();
    echo "<h2>Query Result</h2>";
    echo "Uses left: " . ($row ? $row['usesleft'] : 'N/A');
} else {
    echo "<h2>Error</h2>";
    echo "Query failed";
}