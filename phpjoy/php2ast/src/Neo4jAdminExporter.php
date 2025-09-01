<?php declare(strict_types=1);


require_once "vendor/autoload.php";
require_once 'Exporter.php';

/**
 * @author Malte Skoruppa <skoruppa@cs.uni-saarland.de> shaobaobaoer <shaobaobaoer@126.com>
 */
class Neo4jAdminExporter extends Exporter
{

    /** Used format -- defaults to Neo4J */
    private $format = self::NEO4J_ADMIN_FORMAT;

    /** Delimiter for columns in CSV files */
    private $csv_delim = ",";

    /** Default name of node file */
    const NODE_FILE = "nodes.csv";
    /** Default name of relationship file */
    const REL_FILE = "rels.csv";


    /** Handle for the node file */
    private $nhandle;
    /** Handle for the relationship file */
    private $rhandle;

    /**
     * Constructor, creates file handlers.
     *
     * @param $format     int Format to use for export (neo4j or jexp)
     * @param $nodefile   string Name of the nodes file
     * @param $relfile    int Name of the relationships file
     * @param $startcount *Once* when creating the Neo4jAdmin instance,
     *                    the starting node index may be chosen. Defaults to 0.
     */
    public function __construct($format = self::NEO4J_ADMIN_FORMAT, $nodefile = self::NODE_FILE, $relfile = self::REL_FILE, $startcount = 0)
    {

        $this->format = $format;
        $this->nodecount = $startcount;

        foreach ([$nodefile, $relfile] as $file)
            if (file_exists($file))
                error_log("[WARNING] $file already exists, overwriting it.");

        $this->nhandle = \League\Csv\Writer::createFromPath($nodefile, 'w+');
        $this->rhandle = \League\Csv\Writer::createFromPath($relfile, 'w+');
        $this->nhandle->setOutputBOM(League\Csv\Bom::Utf8);
        $this->nhandle->setEscape(''); // RFC4180Field::Please use directly the setEscape method with the empty escape
        $this->nhandle->insertOne(
            [
                "id:ID", ":LABEL", "type", "flags:string[]", "lineno:int", "code:string",
                "childnum:int", "funcid:int", "classname:string", "namespace:string", "endlineno:int", "name:string", "doccomment:string",
                "fileid:int", "classid:int"
            ]
        );
        $this->rhandle->insertOne(
            [
                ":START_ID", ":END_ID", ":TYPE"
            ]
        );

    }

    /**
     * Destructor, closes file handlers.
     */
    public function __destruct()
    {

    }

    /**
     * Implements the abstract function store_node() declared in the
     * Exporter class to export a node to a CSV file and increase the node
     * counter.
     */
    protected function store_node($label, $type, $flags, $lineno, $code = null, $childnum = null, $funcid = null, $classname = null, $namespace = null, $endlineno = null, $name = null, $doccomment = null, $fileid = null, $classid = null): int
    {
//        ,AST,string,,1,_TODO_REPLACE_CLASS
        if ($type == "string" && (strpos($code, "_TODO_REPLACE_") !== false)) {
            $code = str_replace("_TODO_REPLACE_FUNCTION_", "", $code);
            $code = str_replace("_TODO_REPLACE_CLASS_", "", $code);
        }
        $this->nhandle->insertOne(
            [
                $this->nodecount,
                $label, $type, $flags, $lineno, $code, $childnum, $funcid,
                $classname, $namespace, $endlineno, $name, $doccomment, $fileid, $classid
            ]
        );

        // return the current node index, *then* increment it
        return $this->nodecount++;
    }

    /**
     * Implements the abstract function store_rel() declared in the
     * Exporter class to export a relationship to a CSV file.
     */
    public function store_rel($start, $end, $type)
    {
        $this->rhandle->insertOne(
            [
                $start, $end, $type
            ]
        );
    }

    /**
     * Implements the abstract function quote_and_escape() declared
     * in the Exporter class.
     *
     * Replaces ambiguous signs in $str, namely
     * \ -> \\
     * " -> \"
     * replace newlines for now:
     * \n -> \\n
     * \r -> \\r
     * Additionally, puts quotes around the resulting string.
     */
    protected function quote_and_escape($str): string
    {
        if ($str == null)
            return '';
//        $str = str_replace("\\", "\\\\", $str);
//        $str = str_replace("\n", "\\n", $str);
//        $str = str_replace("\r", "\\r", $str);
//        $str = "\"" . str_replace("\"", "\\\"", $str) . "\"";
        return $str;
    }
}
