<?php
require('fpdf.php');
require('templateutils.php');
/*******************************************************************************
* MyFPDF                                                                       *
*                                                                              *
* Class inheriting directly of FPDF. It redefines any method that does not     *
* behave accordingly to what we would expect.                                  *
*                                                                              *
* Date:    19.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class MyFPDF extends FPDF
{
	protected $utils;               // Utilities functions for templates

	/*******************************************************************************
	*			   					Public methods							       *
	*******************************************************************************/

	function __construct($utils, $orientation='P', $unit='mm', $size='A4')
	{
	    $this->utils = $utils;
	    
		parent::__construct($orientation, $unit, $size);
	}

	function MyImage($MinX, $MinY, $MaxX, $MaxY, $filename)
	{
	    // 150 DPI
		parent::Image($filename, $MinX, $MinY, $MaxX - $MinX);
	}

    /**
     * Custom wrapper for putting the given text in a box. It will try to place all text inside the box. If it cannot,
     * it won't do anything and will return the original text.
     * @param $MinX                       float position of the box
     * @param $MinY                       float position of the box
     * @param $MaxX                       float position of the box
     * @param $MaxY                       float position of the box
     * @param $txt                        text to insert
     * @param $height                     float height of the box
     * @param bool $preventOverflow       set to true to avoid printing anything if overflow is detected.
     * @return string       will return empty string if the text is put, or the original text if it was overflowing.
     */
	function MyMultiCell($MinX, $MinY, $MaxX, $MaxY, $txt, $height, $preventOverflow=false)
    {
		parent::SetXY($MinX, $MinY);
		$cells = [];
		$w = $MaxX - $MinX;
		$h = $height;
		$maxline = ($MaxY - $MinY) / $height;
        //Output text with automatic or explicit line breaks, at most $maxline lines
        $cw=&$this->CurrentFont['cw'];
        if($w==0)
            $w=$this->w-$this->rMargin-$this->x;
        $wmax=($w-2*$this->cMargin)*1000/$this->FontSize;
        $s=str_replace("\r",'',$txt);
        $nb=strlen($s);
        if($nb>0 && $s[$nb-1]=="\n")
            $nb--;
        $b=0;
        $sep=-1;
        $i=0;
        $j=0;
        $l=0;
        $ns=0;
        $nl=1;
        while($i<$nb)
        {
            //Get next character
            $c=$s[$i];
            if($c=="\n")
            {
                //Explicit line break
                if($this->ws>0)
                {
                    $this->ws=0;
                    if ($preventOverflow) {
                        array_push($cells, '0 Tw');
                    } else {
                        $this->_out('0 Tw');
                    }
                }
                if ($preventOverflow) {
                    array_push($cells, [$w,$h,substr($s,$j,$i-$j),$b,2,'J',false]);
                } else {
                    $this->Cell($w,$h,substr($s,$j,$i-$j),$b,2,'J',false);
                }
                $i++;
                $sep=-1;
                $j=$i;
                $l=0;
                $ns=0;
                $nl++;
                if($maxline && $nl>$maxline)
                    return substr($s,$i);
                continue;
            }
            if($c==' ')
            {
                $sep=$i;
                $ls=$l;
                $ns++;
            }
            $l+=$cw[$c];
            if($l>$wmax)
            {
                //Automatic line break
                if($sep==-1)
                {
                    if($i==$j)
                        $i++;
                    if($this->ws>0)
                    {
                        $this->ws=0;
                        if ($preventOverflow) {
                            array_push($cells, '0 Tw');
                        } else {
                            $this->_out('0 Tw');
                        }
                    }
                    if ($preventOverflow) {
                        array_push($cells, [$w,$h,substr($s,$j,$i-$j),$b,2,'J',false]);
                    } else {
                        $this->Cell($w,$h,substr($s,$j,$i-$j),$b,2,'J',false);
                    }
                }
                else
                {
                    $this->ws=($ns>1) ? ($wmax-$ls)/1000*$this->FontSize/($ns-1) : 0;
                    if ($preventOverflow) {
                        array_push($cells, sprintf('%.3F Tw',$this->ws*$this->k));
                    } else {
                        $this->_out(sprintf('%.3F Tw',$this->ws*$this->k));
                    }
                    if ($preventOverflow) {
                        array_push($cells, [$w,$h,substr($s,$j,$sep-$j),$b,2,'J',false]);
                    } else {
                        $this->Cell($w,$h,substr($s,$j,$sep-$j),$b,2,'J',false);
                    }
                    $i=$sep+1;
                }
                $sep=-1;
                $j=$i;
                $l=0;
                $ns=0;
                $nl++;
                if($maxline && $nl>$maxline)
                {
                    if($this->ws>0)
                    {
                        $this->ws=0;
                        if ($preventOverflow) {
                            array_push($cells, '0 Tw');
                        } else {
                            $this->_out('0 Tw');
                        }
                    }
                    return substr($s,$i);
                }
            }
            else
                $i++;
        }
        //Last chunk
        if($this->ws>0)
        {
            $this->ws=0;
            if ($preventOverflow) {
                array_push($cells, '0 Tw');
            } else {
                $this->_out('0 Tw');
            }
        }

        //  If we arrive up to here, it means the text fits in the box and we can print it.
        if ($preventOverflow) {
            array_push($cells, [$w,$h,substr($s,$j,$i-$j),$b,2,'J',false]);
            foreach ($cells as $cell) {
                if (is_array($cell)) {
                    $this->Cell(...$cell);
                } else {
                    $this->_out($cell);
                }
            }
        } else {
            $this->Cell($w,$h,substr($s,$j,$i-$j),$b,2,'J',false);
        }
        $this->x=$this->lMargin;
        return '';
    }

	function MyAddPage($showTemplate=true, $orientation='', $size='', $rotation=0)
	{
		parent::AddPage($orientation, $size, $rotation);
	    // We show template only if the user wants to
        $template = $this->utils->GetTemplateForPageNo($this->PageNo());
	    if($showTemplate && $template->GetFilename() != null)
	    {
		    $this->Image($template->GetFilename(), 0, 0, $this->w, $this->h);
	    }
	    // We always display header, if it exists (for blank additional pages for pictures)
	    if($template->GetHeader() != null)
	    {
            $this->SetFont('Arial', '', 10);
	        $template->GetHeader()->InsertIntoPDF($this);
            $this->SetFont('Montserrat', 'R', 14);
	        return true;
	    }
		return false;
	}
	
	function GetWidth()
	{
	    return $this->w;
	}
	
	function GetHeight()
	{
	    return $this->h;
	}
}
?>
