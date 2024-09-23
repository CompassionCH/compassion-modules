<?php
/*******************************************************************************
* Text                                                                         *
*                                                                              *
* Date:    22.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class Text
{
    protected $text;
    protected $type;

    function __construct($filename, $type)
    {
        $this->text = iconv(
            'UTF-8', 'ISO-8859-15//TRANSLIT', file_get_contents($filename)
            );
        $this->type = $type;
    }

    function GetText()
    {
        return $this->text;
    }

    function SetText($text)
    {
        $this->text = $text;
    }

    function HasType($type)
    {
        return $this->type == $type;
    }
}
?>
