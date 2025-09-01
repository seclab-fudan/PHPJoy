<?php declare(strict_types=1);

use ast\flags;

const AST_DUMP_LINENOS = 1;
const AST_DUMP_EXCLUDE_DOC_COMMENT = 2;

function get_flag_info(): array
{
    static $info;
    if ($info !== null) {
        return $info;
    }
    foreach (ast\get_metadata() as $data) {
        if (empty($data->flags)) {
            continue;
        }
        $flagMap = [];
        foreach ($data->flags as $fullName) {
            $shortName = substr($fullName, strrpos($fullName, '\\') + 1);
            $flagMap[constant($fullName)] = $shortName;
        }

        $info[(int)$data->flagsCombinable][$data->kind] = $flagMap;
    }

    return $info;
}

function format_flags(int $kind, int $flags): string
{
    list($exclusive, $combinable) = get_flag_info();
    if (isset($exclusive[$kind])) {
        $flagInfo = $exclusive[$kind];
        if (isset($flagInfo[$flags])) {
            return "{$flagInfo[$flags]} ($flags)";
        }
    } else if (isset($combinable[$kind])) {
        $flagInfo = $combinable[$kind];
        $names = [];
        foreach ($flagInfo as $flag => $name) {
            if ($flags & $flag) {
                $names[] = $name;
            }
        }
        if (!empty($names)) {
            return implode(" | ", $names) . " ($flags)";
        }
    }
    return (string)$flags;
}

/** Dumps abstract syntax tree */
function ast_dump($ast, int $options = 0): string
{
    if ($ast instanceof ast\Node) {
        $result = ast\get_kind_name($ast->kind);

        if ($options & AST_DUMP_LINENOS) {
            $result .= " @ $ast->lineno";
            if (isset($ast->endLineno)) {
                $result .= "-$ast->endLineno";
            }
        }
        if (ast\kind_uses_flags($ast->kind) || $ast->flags != 0) {
            $result .= "\n    flags: " . format_flags($ast->kind, $ast->flags);
        }
        foreach ($ast->children as $i => $child) {
            if (($options & AST_DUMP_EXCLUDE_DOC_COMMENT) && $i === 'docComment') {
                continue;
            }
            $result .= "\n    $i: " . str_replace("\n", "\n    ", ast_dump($child, $options));
        }
        return $result;
    } else if ($ast === null) {
        return 'null';
    } else if (is_string($ast)) {
        return "\"$ast\"";
    } else {
        return (string)$ast;
    }
}

/**
 * @throws \League\Csv\InvalidArgument
 * @throws \League\Csv\CannotInsertRecord
 * @throws ReflectionException
 */
function write_predefined_map($current_function_map, $current_class_map, $current_const_map)
{
    # const | function | class
    $const_handler = \League\Csv\Writer::createFromPath("predefined.csv", 'w+');
    $const_handler->setOutputBOM(League\Csv\Bom::Utf8);
    $const_handler->setEscape(''); // RFC4180Field::Please use directly the setEscape method with the empty escape
    $const_handler->insertOne(
        [
            "name", "value", "category",
        ]
    );
    foreach ($current_function_map as $key => $value) {
        $const_handler->insertOne(
            [
                $value, "", "function"
            ]
        );
    }
    foreach ($current_class_map as $key => $value) {
        $const_handler->insertOne(
            [
                $value, "", "class"
            ]
        );
        $r = new ReflectionClass($value);
        if (!empty(get_class_methods($value))) {
            foreach (get_class_methods($value) as $class_method) {
                if ((substr($class_method, 0, 2) == "__") && $class_method != "__construct") {
                    continue;
                }
                $const_handler->insertOne(
                    [
                        $class_method, $value, $r->getMethod($class_method)->isStatic() ? "static_method" : "dynamic_method"
                    ]
                );
//                echo 1;
            }
        }
    }
    foreach ($current_const_map as $key => $value) {
        $const_handler->insertOne(
            [
                $key, $value, "const"
            ]
        );
    }
}

/**
 * @throws ReflectionException
 */
function write_prefefined_file($current_function_map, $current_class_map, $input_file_dir)
{
    $myfile = fopen($input_file_dir . DIRECTORY_SEPARATOR . 'PHPJOERN_PREDEFINE.php', "w") or die("Unable to open file!");
    fwrite($myfile, "<?php\n");
    foreach ($current_function_map as $key => $value) {
        if (strpos($value, "\\")) {
            echo $value;
            continue;
        }
        fwrite($myfile, "function _TODO_REPLACE_FUNCTION_" . $value . "(){};");
    }
    foreach ($current_class_map as $key => $value) {
        // if value has /?
        if (strpos($value, "\\")) {
            echo $value;
            continue;
        }
        fwrite($myfile, "class _TODO_REPLACE_CLASS_" . $value . "{");

        $r = new ReflectionClass($value);
        if (!empty(get_class_methods($value))) {
            foreach (get_class_methods($value) as $class_method) {
                if ((substr($class_method, 0, 2) == "__") && $class_method != "__construct") {
                    # ignore magic methods
                    continue;
                }
                fwrite($myfile, ($r->getMethod($class_method)->isStatic() ? "static function " : "function ") . $class_method . "(){} ");
            }
        }
        fwrite($myfile, "  };");
    }
    fclose($myfile);
    return $input_file_dir . DIRECTORY_SEPARATOR . 'PHPJOERN_PREDEFINE.php';
}