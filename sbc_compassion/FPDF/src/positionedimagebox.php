<?php
/*******************************************************************************
* Templates                                                                    *
*                                                                              *
* Date:    22.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class PositionedImageBox extends PositionedObject 
{
    protected $hasBeenUsed;      // Tells whether an image box has been used or not yet

	function __construct($minX, $minY, $maxX, $maxY)
	{
		$this->hasBeenUsed = false;
		
		parent::__construct($minX, $minY, $maxX, $maxY);
	}

	function HasBeenUsed()
	{
		return $this->hasBeenUsed;
	}
	
	function SetHasBeenUsed($hasBeenUsed)
	{
	    $this->hasBeenUsed = $hasBeenUsed;
	}
}
?>
