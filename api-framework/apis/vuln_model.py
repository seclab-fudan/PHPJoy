import json

ARBITRARY_FILE_INCLUDE = "Arbitrary File Include"
ARBITRARY_FILE_READ = "Arbitrary File Read"
ARBITRARY_FILE_DELETE = "Arbitrary File Delete"
ARBITRARY_FILE_WRITE = "Arbitrary File Write"
XSS = "Server-Side XSS"
COMMAND_INJECTION = "Command Injection"
CODE_INJECTION = "Code Injection"
DIRECTORY_TRAVERSAL = "Directory Traversal"
EXECUTABLE_FILE_UPLOAD = "Executable File Upload"
OPEN_REDIRECT = "Open Redirect"
PHP_OBJECT_INJECTION = "PHP Object Injection"
SQL_INJECTION = "SQL Injection"
SSRF = "Server-Side Request Forgery (SSRF)"
ALL_SINK = "All vulnerability"
XSS_SQLI = "XSS AND SQLI"

VULN_TYPE_ID_TO_STRING = dict((
    (1, ALL_SINK),
    (3, CODE_INJECTION),
    (4, COMMAND_INJECTION),
    (5, DIRECTORY_TRAVERSAL),
    (6, EXECUTABLE_FILE_UPLOAD),
    (7, ARBITRARY_FILE_INCLUDE),
    (8, PHP_OBJECT_INJECTION),
    (9, SQL_INJECTION),
    (10, XSS),
    (11, SSRF),
    (12, ARBITRARY_FILE_WRITE),
    (13, OPEN_REDIRECT),
    (0, XSS_SQLI),)
)

STRING_TO_VULN_TYPE = {v: k for k, v in VULN_TYPE_ID_TO_STRING.items()}

POTENTIAL_SOURCE_MODEL = {
    "_POST", "_GET", "_REQUESTS", "_COOKIE", "_FILE"
}

BASIC_SANITIZE_FUNCTIONS = {
    "preg_replace", "preg_match",
    "md5", "sha1", "crypt", "json_encode", "is_numberic", "intval",
    "addslash",
    # 	// securing functions in if-clause
    # 	// list not used, all if clause dependencies detected anyway
    'is_bool', 'is_double', 'is_float', 'is_real', 'is_long', 'is_int', 'is_integer', 'is_null', 'is_numeric',
    'is_finite', 'is_infinite', 'ctype_alnum', 'ctype_alpha', 'ctype_cntrl', 'ctype_digit', 'ctype_xdigit',
    'ctype_upper', 'ctype_lower', 'ctype_space', 'in_array', 'preg_match', 'preg_match_all', 'fnmatch', 'ereg',
    'eregi'  # // securing functions for every vulnerability
    'intval', 'floatval', 'doubleval', 'filter_input', 'urlencode', 'rawurlencode', 'round', 'floor', 'strlen',
    'strrpos', 'strpos', 'strftime', 'strtotime', 'md5', 'md5_file', 'sha1', 'sha1_file', 'crypt', 'crc32', 'hash',
    'mhash', 'hash_hmac', 'password_hash', 'mcrypt_encrypt', 'mcrypt_generic', 'base64_encode', 'ord', 'sizeof',
    'count', 'bin2hex', 'levenshtein', 'abs', 'bindec', 'decbin', 'dechex', 'decoct', 'hexdec', 'rand', 'max', 'min',
    'metaphone', 'tempnam', 'soundex', 'money_format', 'number_format', 'date_format', 'filetype', 'nl_langinfo',
    'bzcompress', 'convert_uuencode', 'gzdeflate', 'gzencode', 'gzcompress', 'http_build_query', 'lzf_compress',
    'zlib_encode', 'imap_binary', 'iconv_mime_encode', 'bson_encode', 'sqlite_udf_encode_binary', 'session_name',
    'readlink', 'getservbyport', 'getprotobynumber', 'gethostname', 'gethostbynamel', 'gethostbyname',
    # // functions that insecures the string again
    'base64_decode', 'htmlspecialchars_decode', 'html_entity_decode', 'bzdecompress', 'chr', 'convert_uudecode',
    'gzdecode', 'gzinflate', 'gzuncompress', 'lzf_decompress', 'rawurldecode', 'urldecode', 'zlib_decode',
    'imap_base64', 'imap_utf7_decode', 'imap_mime_header_decode', 'iconv_mime_decode', 'iconv_mime_decode_headers',
    'hex2bin', 'quoted_printable_decode', 'imap_qprint', 'mb_decode_mimeheader', 'bson_decode',
    'sqlite_udf_decode_binary', 'utf8_decode', 'recode_string', 'recode',
    # // securing functions for SQLi
    'addslashes', 'dbx_escape_string', 'db2_escape_string', 'ingres_escape_string', 'maxdb_escape_string',
    'maxdb_real_escape_string', 'mysql_escape_string', 'mysql_real_escape_string', 'mysqli_escape_string',
    'mysqli_real_escape_string', 'pg_escape_string', 'pg_escape_bytea', 'sqlite_escape_string',
    'sqlite_udf_encode_binary', 'cubrid_real_escape_string',
    # // securing functions for XSS
    'htmlentities', 'htmlspecialchars', 'highlight_string', }

EXTERNAL_SANITIZE_FUNCTIONS = {
    XSS: ["htmlspecialchars", "htmlentities", "strip_tags"],
    SQL_INJECTION: ["mysql_real_escape_string", "pg_escape_string", "sqlite_escape_string"],
    COMMAND_INJECTION: ["escapeshellarg", "escapeshellcmd"]
}

POTENTIAL_SINK_MODEL = {
    ARBITRARY_FILE_INCLUDE:
        {"include", "require", "include_once", "require_once"},
    ARBITRARY_FILE_READ:
        {"file", "file_get_contents", "readfile", "fopen"},
    ARBITRARY_FILE_DELETE:
        {"unlink", "rmdir"},
    ARBITRARY_FILE_WRITE:
        {"file_put_contents", "fopen", "fwrite"},
    XSS:
        {"echo", "print", "print_r", "exit", "die", "printf", "vprintf"},
    COMMAND_INJECTION:
        {"exec", "passthru", "proc_open", "system", "shell_exec", "popen", "pcntl_exec"},
    CODE_INJECTION:
        {"eval", "create_function", "assert", "array_map",
         },
    DIRECTORY_TRAVERSAL:
        {"fopen", "dir", "dirname", "opendir", "scandir"},
    EXECUTABLE_FILE_UPLOAD:
        {"copy", "fopen", "move_uploaded_file"},
    OPEN_REDIRECT: {"header"},
    PHP_OBJECT_INJECTION: {"unserialize"},
    SSRF: {"curl_exec", "file_get_contents", "fsockopen"},
    SQL_INJECTION: {
        'dba_open', 'dba_popen', 'dba_insert', 'dba_fetch', 'dba_delete', 'dbx_query', 'odbc_do', 'odbc_exec',
        'odbc_execute', 'db2_execute', 'fbsql_db_query', 'fbsql_query', 'ibase_query', 'ibase_execute', 'ifx_query',
        'ifx_do', 'ingres_query', 'ingres_execute', 'ingres_unbuffered_query', 'msql_db_query', 'msql_query', 'msql',
        'mssql_query', 'mssql_execute', 'mysql_db_query', 'mysql_query', 'mysql_unbuffered_query',
        'mysqli_stmt_execute', 'mysqli_query', 'mysqli_real_query', 'mysqli_master_query', 'oci_execute', 'ociexecute',
        'ovrimos_exec', 'ovrimos_execute', 'ora_do', 'ora_exec', 'pg_query', 'pg_send_query', 'pg_send_query_params',
        'sqlite_open', 'sqlite_popen', 'sqlite_array_query', 'arrayQuery', 'singleQuery', 'sqlite_query', 'sqlite_exec',
        'sqlite_single_query', 'sqlite_unbuffered_query', 'sybase_query', 'sybase_unbuffered_query', "query"},
    XSS_SQLI: {
        'dba_open', 'dba_popen', 'dba_insert', 'dba_fetch', 'dba_delete', 'dbx_query', 'odbc_do', 'odbc_exec',
        'odbc_execute', 'db2_execute', 'fbsql_db_query', 'fbsql_query', 'ibase_query', 'ibase_execute', 'ifx_query',
        'ifx_do', 'ingres_query', 'ingres_execute', 'ingres_unbuffered_query', 'msql_db_query', 'msql_query', 'msql',
        'mssql_query', 'mssql_execute', 'mysql_db_query', 'mysql_query', 'mysql_unbuffered_query',
        'mysqli_stmt_execute', 'mysqli_query', 'mysqli_real_query', 'mysqli_master_query', 'oci_execute', 'ociexecute',
        'ovrimos_exec', 'ovrimos_execute', 'ora_do', 'ora_exec', 'pg_query', 'pg_send_query', 'pg_send_query_params',
        'sqlite_open', 'sqlite_popen', 'sqlite_array_query', 'arrayQuery', 'singleQuery', 'sqlite_query', 'sqlite_exec',
        'sqlite_single_query', 'sqlite_unbuffered_query', 'sybase_query', 'sybase_unbuffered_query',
        "echo", "print", "print_r", "exit", "die", "printf", "vprintf"
    },
    ALL_SINK: {
        "include", "require", "include_once", "require_once",
        "file", "file_get_contents", "readfile",
        "unlink", "rmdir",
        "file_put_contents", "fopen", "fwrite",
        "echo", "print",
        "exec", "passthru", "proc_open", "system", "shell_exec", "popen", "pcntl_exec",
        "eval", "create_function", "assert", "array_map",
        "dir", "dirname", "opendir", "scandir",
        "copy", "move_uploaded_file",
        "header",
        "unserialize",
        "curl_exec", "file_get_contents", "fsockopen",
        "pg_query", "mysql_query", "mysqli_query",
    }
}
