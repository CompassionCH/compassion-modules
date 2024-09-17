<?php
/*******************************************************************************
* Header                                                                        *
*                                                                              *
* Date:    22.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class Header extends PositionedObject
{
    protected $text;
    protected $height;

    function __construct($filename, $minX, $minY, $maxX, $maxY, $height=TemplateUtils::DEFAULT_CELL_HEIGHT)
    {
        $this->text = utf8_decode(file_get_contents($filename));
        $this->height = $height;

        parent::__construct($minX, $minY, $maxX, $maxY);
    }

    function InsertIntoPDF($pdf)
    {
        $pdf->MyMultiCell($this->minX, $this->minY, $this->maxX, $this->maxY, $this->text, $this->height);
    }
}
?>
