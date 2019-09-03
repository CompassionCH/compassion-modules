<?php
/*******************************************************************************
* PositionedObject                                                             *
*                                                                              *
* Date:    21.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class PositionedObject
{
	protected $minX;						// Minimum X position
	protected $minY;						// Minimum Y position
	protected $maxX;						// Maximum X position
	protected $maxY;						// Maximum Y position

	function __construct($minX, $minY, $maxX, $maxY)
	{
		$this->minX = $minX;
		$this->minY = $minY;
		$this->maxX = $maxX;
		$this->maxY = $maxY;
	}
	
	function GetCoordinates()
	{
	    return array($this->minX, $this->minY, $this->maxX, $this->maxY);
	}

	function GetMinX()
	{
		return $this->minX;
	}

	function GetMinY()
	{
		return $this->minY;
	}

	function GetMaxX()
	{
		return $this->maxX;
	}

	function GetMaxY()
	{
		return $this->maxY;
	}

	function GetWidth()
	{
		return $this->maxX - $this->minX;
	}

	function GetHeight()
	{
		return $this->maxY - $this->minY;
	}
}
?>
