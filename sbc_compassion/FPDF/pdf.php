<?php
require('src/myfpdf.php');
require('src/pdfcreator.php');

/**
* Equivalent of a main in most programming languages. Will be launched directly
* from Python or manually from terminal. It expects a JSON description of the
* PDF to generate. Find more information about that in the README.
*/

$pdf_name = $argv[1];
$parameters = json_decode($argv[2], true);
echo var_export($parameters) . "\n";
$pdfCreator = new PDFCreator($parameters);
$pdfCreator->createPDF($pdf_name);
?>
