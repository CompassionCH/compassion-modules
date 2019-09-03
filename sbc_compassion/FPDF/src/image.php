<?php
/*******************************************************************************
* Image                                                                        *
*                                                                              *
* Date:    22.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class Image
{
    protected $filename;        // Filename of the image to display
    protected $width;           // Width of the image
    protected $height;          // Height of the image

	function __construct($filename)
	{
		$this->filename = $filename;
		
        $size = getimagesize($filename);
        $this->width = $size[0] / 2.83464;
        $this->height = $size[1] / 2.83464;
	}

	function GetFilename()
	{
		return $this->filename;
	}
	
	function InsertIntoPDF($pdf, $minX, $minY, $maxX, $maxY)
	{
        // We get the maximal possible width and length of the image
	    $maxWidth = $maxX - $minX;
	    $maxHeight = $maxY - $minY;
        
        /* We resize images only downward, never upward. If we need to rescale one down,
           we look for the smallest ratio (originalSize / maxSize) to scale the image */
        $factor = min(min(1, $maxWidth / $this->width), $maxHeight / $this->height);
        // We compute the actual width and length of the image
        $width = (int)($this->width * $factor);
        $height = (int)($this->height * $factor);
	    
	    // Finally, we center the image in the image defined zone
	    $newMinX = $minX + ($maxWidth - $width) / 2;
	    $newMinY = $minY + ($maxHeight - $height) / 2;
	    $newMaxX = $maxX - ($maxWidth - $width) / 2;
	    $newMaxY = $maxY - ($maxHeight - $height) / 2;
	    
		$pdf->MyImage($newMinX, $newMinY, $newMaxX, $newMaxY, $this->filename);
	}
}
?>
