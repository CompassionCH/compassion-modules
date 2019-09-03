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
	protected $templates;           // Templates for the PDF document
	protected $utils;               // Utilities functions for templates

	/*******************************************************************************
	*			   					Public methods							       *
	*******************************************************************************/

	function __construct($templates, $utils, $orientation='P', $unit='mm', $size='A4')
	{
	    $this->templates = $templates;
	    $this->utils = $utils;
	    
		parent::__construct($orientation, $unit, $size);
	}

	function MyImage($MinX, $MinY, $MaxX, $MaxY, $filename)
	{
		parent::Image($filename, $MinX, $MinY, $MaxX - $MinX);
	}

    function MyMultiCell($MinX, $MinY, $MaxX, $MaxY, $txt, $height, $border=0, $align='J', $fill=false)
    {
		parent::SetXY($MinX, $MinY);
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
        if($border)
        {
            if($border==1)
            {
                $border='LTRB';
                $b='LRT';
                $b2='LR';
            }
            else
            {
                $b2='';
                if(is_int(strpos($border,'L')))
                    $b2.='L';
                if(is_int(strpos($border,'R')))
                    $b2.='R';
                $b=is_int(strpos($border,'T')) ? $b2.'T' : $b2;
            }
        }
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
                    $this->_out('0 Tw');
                }
                $this->Cell($w,$h,substr($s,$j,$i-$j),$b,2,$align,$fill);
                $i++;
                $sep=-1;
                $j=$i;
                $l=0;
                $ns=0;
                $nl++;
                if($border && $nl==2)
                    $b=$b2;
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
                        $this->_out('0 Tw');
                    }
                    $this->Cell($w,$h,substr($s,$j,$i-$j),$b,2,$align,$fill);
                }
                else
                {
                    if($align=='J')
                    {
                        $this->ws=($ns>1) ? ($wmax-$ls)/1000*$this->FontSize/($ns-1) : 0;
                        $this->_out(sprintf('%.3F Tw',$this->ws*$this->k));
                    }
                    $this->Cell($w,$h,substr($s,$j,$sep-$j),$b,2,$align,$fill);
                    $i=$sep+1;
                }
                $sep=-1;
                $j=$i;
                $l=0;
                $ns=0;
                $nl++;
                if($border && $nl==2)
                    $b=$b2;
                if($maxline && $nl>$maxline)
                {
                    if($this->ws>0)
                    {
                        $this->ws=0;
                        $this->_out('0 Tw');
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
            $this->_out('0 Tw');
        }
        if($border && is_int(strpos($border,'B')))
            $b.='B';
        $this->Cell($w,$h,substr($s,$j,$i-$j),$b,2,$align,$fill);
        $this->x=$this->lMargin;
        return '';
    }

	function MyAddPage($showTemplate=true, $orientation='', $size='', $rotation=0)
	{
		parent::AddPage($orientation, $size, $rotation);
	    // We show template only if the user wants to
        $template = $this->utils->GetTemplateForPageNo($this->PageNo());
	    if($showTemplate)
	    {
		    $this->Image($template->GetFilename(), 0, 0, $this->w, $this->h);
	    }
	    // We always display header, if it exists (for blank additional pages for pictures)
	    if($template->GetHeader() != null)
	    {
	        $template->GetHeader()->InsertIntoPDF($this);
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
