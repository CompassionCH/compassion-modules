<?php
/*******************************************************************************
* TemplateUtils                                                                *
*                                                                              *
* Date:    22.08.2019                                                          *
* Author:  Théo Nikles (theo.nikles@gmail.com)                                 *
*******************************************************************************/

class TemplateUtils
{
    const DEFAULT_CELL_HEIGHT = 6;
    
    public $templates;
    private $numberOfPages;
    public  $overflowTemplate;    // Can be used for overflow pages instead of repeating the template => Template
    private $oddPageNumber;
    private $oneOrTwoPages;
    
    function __construct($templates, $numberOfPages, $overflowTemplate)
    {
        $this->templates = $templates;
        $this->numberOfPages = min($numberOfPages, count($templates));
        $this->oddPageNumber = count($templates) % 2 != 0;
        $this->oneOrTwoPages = count($templates) <= 2;
        $this->overflowTemplate = $overflowTemplate;
    }
    
    function GetTemplateForPageNo($pageNo)
    {
        // Not every page was displayed once, we return the page at index pageNo.
        if($pageNo <= $this->numberOfPages)
        {
            return $this->templates[$pageNo - 1];
        }
        // If an overflow template is given, we use it systematically for the additional pages.
        if (isset($this->overflowTemplate) and $this->overflowTemplate != false) {
            // Overflow template will always have an available textBox, because we repeat it many times needed.
            $this->overflowTemplate->ResetTextBoxes();
            return $this->overflowTemplate;
        }
        // If we still have template pages to render, use them
        if ($pageNo <= count($this->templates)) {
            return $this->templates[$pageNo - 1];
        }
        // Odd number of template pages, the last page is repeated as long as needed.
        if($this->oddPageNumber)
        {
            return $this->templates[$this->numberOfPages - 1];
        }
        // Even number of template pages, we have to find if we display even or odd index.
        return $this->templates[($pageNo - 1) % 2 + ($this->oneOrTwoPages ? 0 : 2)];
    }

    function addExtraPage($pageNo) {
        array_splice($this->templates, $pageNo, 0, array($this->overflowTemplate));
        $this->numberOfPages++;
    }
}
?>
