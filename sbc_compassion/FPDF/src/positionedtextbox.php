<?php
require_once('positionedobject.php');
/*******************************************************************************
* PositionedText                                                               *
*                                                                              *
* Date:    21.08.2019                                                          *
* Author:  Théo Nikles	                                                       *
*******************************************************************************/

class PositionedTextBox extends PositionedObject
{
    protected $height;      // Height of the text cells
    protected $type;        // Type of the text cells (either "O" for original or "T" for translation)
	protected $used;		// Stores if the box is filled with text or not

	function __construct($minX, $minY, $maxX, $maxY, $type, $height=6)
	{
		$this->height = $height;
		$this->type = $type;
		
		parent::__construct($minX, $minY, $maxX, $maxY);
	}

	function GetHeight()
	{
		return $this->height;
	}

	function GetType()
	{
		return $this->type;
	}

	function Use()
	{
		$this->used = true;
	}

	function Available()
	{
		return !$this->used;
	}

	function Reset()
	{
		$this->used = false;
	}
}
?>
