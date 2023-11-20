<?php
require('positionedtextbox.php');
require('positionedimagebox.php');
require('header.php');
/*******************************************************************************
* Templates                                                                    *
*                                                                              *
* Date:    22.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class Template
{
    protected $filename;
    protected $header;
    protected $textBoxes;
    protected $imageBoxes;

    function __construct($filename, $header, $textBoxes, $imageBoxes)
    {
        $this->filename = $filename;
        if(count($header) != 0)
        {
            $this->header = new Header(...$header);
        }

        $boxes = array();
        foreach ($textBoxes as $textBox)
        {
            array_push($boxes, new PositionedTextBox(...$textBox));
        }
        $this->textBoxes = $boxes;

        $boxes = array();
        foreach ($imageBoxes as $imageBox)
        {
            array_push($boxes, new PositionedImageBox(...$imageBox));
        }
        $this->imageBoxes = $boxes;
    }

    function GetFilename()
    {
        return $this->filename;
    }

    function GetHeader()
    {
        return $this->header;
    }

    function GetTextBoxes()
    {
        return $this->textBoxes;
    }

    function GetImageBoxes()
    {
        return $this->imageBoxes;
    }

    function HasRemainingImageBox()
    {
        foreach ($this->imageBoxes as $imageBox)
        {
            if(!$imageBox->HasBeenUsed())
            {
                return true;
            }
        }
        return false;
    }

    function ResetImageBoxes()
    {
        foreach ($this->imageBoxes as $imageBox)
        {
            $imageBox->SetHasBeenUsed(false);
        }
    }

    function ResetTextBoxes()
    {
        foreach ($this->textBoxes as $textBox)
        {
            $textBox->Reset();
        }
    }
}
?>
