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
    
    private $templates;
    private $numberOfTemplates;
    private $oddPageNumber;
    private $oneOrTwoPages;
    
    function __construct($templates)
    {
        $this->templates = $templates;
        $this->numberOfTemplates = count($templates);
        $this->oddPageNumber = $this->numberOfTemplates % 2 != 0;
        $this->oneOrTwoPages = $this->numberOfTemplates <= 2;
    }
    
    function GetTemplateForPageNo($pageNo)
    {
        // Not every page was displayed once, we return the page at index pageNo.
        if($pageNo <= $this->numberOfTemplates)
        {
            return $this->templates[$pageNo - 1];
        }
        // Odd number of template pages, the last page is repeated as long as needed.
        if($this->oddPageNumber)
        {
            return $this->templates[$this->numberOfTemplates - 1];
        }
        // Even number of template pages, we have to find if we display even or odd index.
        return $this->templates[($pageNo - 1) % 2 + ($this->oneOrTwoPages ? 0 : 2)];
    }
}
?>
