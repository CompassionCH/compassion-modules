<?php
require('image.php');
require('template.php');
require('text.php');
/*******************************************************************************
* PDFCreator                                                                   *
*                                                                              *
* Date:    21.08.2019                                                          *
* Author:  Théo Nikles	                                                       *
*******************************************************************************/

class PDFCreator
{
  protected $templates;           // Array of templates                       => array[Template]
	protected $images;              // Array of images                          => array[Image]
	protected $texts;               // Array of the text zones                  => array[Text]
	protected $utils;               // Utilities that provides useful functions => TemplateUtils

	protected $headerOnLastPage;


    /**
    *
    */
    function __construct($params)
    {
        $this->templates = $this->ComputeArray($params, 'templates', function($template)
            {
                return new Template(...$template);
            }
        );

        $this->images = $this->ComputeArray($params, 'images', function($img)
            {
                return new Image($img);
            }
        );

        $this->texts = $this->ComputeArray($params, 'texts', function($text)
            {
                return new Text(...$text);
            }
        );


        // We don't accept PDFs with no template.
        if(count($this->templates) == 0)
        {
            throw new Exception("No templates provided, cannot generate PDF");
        }
        $this->utils = new TemplateUtils($this->templates);
        $headerOnLastPage = false;
    }


    /**
    *
    */
    function createPDF()
    {
        // SET UP
        $pdf = new MyFPDF($this->templates, $this->utils);
        $pdf->SetFont('Arial', '', 12);

        $consecutiveEmptyPages = 0;
        // CREATE NEW PAGE AND FILL IT WITH CONTENT
        while (!empty($this->texts))
        {
	        $headerOnLastPage = $pdf->MyAddPage();
            $template = $this->utils->GetTemplateForPageNo($pdf->PageNo());

	        $emptyPage = $this->InsertText($pdf, $template);

	        $this->InsertImages($pdf, $template);

	        $consecutiveEmptyPages = $this->PreventInfiniteLoop($emptyPage, $consecutiveEmptyPages);
        }

        // COMPLETE THE END OF THE PDF AND WRITE IT
        $this->CompleteAndWritePDF($pdf);
    }


    /**
    *
    */
    private function InsertImages($pdf, $template)
    {
        $imageBoxes = $template->GetImageBoxes();
        while(!empty($this->images) && $template->HasRemainingImageBox())
        {
            foreach($imageBoxes as $imageBox)
            {
                if(!$imageBox->HasBeenUsed())
                {
                    $image = $this->images[0];
                    $image->InsertIntoPDF($pdf, ...$imageBox->GetCoordinates());
                    array_splice($this->images, 0, 1);
                    $imageBox->SetHasBeenUsed(true);
                }
            }
        }
        $template->ResetImageBoxes();
    }


    /**
    *
    */
    private function InsertText($pdf, $template)
    {
        $emptyPage = true;
        foreach (range(count($this->texts), 1) as $i)
        {
            $text = $this->texts[$i - 1];
            foreach ($template->GetTextBoxes() as $textBox)
            {
                if($text->HasType($textBox->GetType()))
                {
                    $emptyPage = false;
                    $text->SetText($pdf->MyMultiCell($textBox->GetMinX(), $textBox->GetMinY(), $textBox->GetMaxX(), $textBox->GetMaxY(), $text->GetText(), $height=$textBox->GetHeight()));
                    if($text->GetText() == "")
                    {
                        array_splice($this->texts, $i - 1, 1);
                    }
                }
            }
        }
        return $emptyPage;
    }


    /**
    *
    */
    private function PreventInfiniteLoop($emptyPage, $pagesWithoutText)
    {
        if($emptyPage)
        {
            $pagesWithoutText++;
            if($pagesWithoutText >= 4)
            {
                throw new Exception("Could not generate PDF, something went wrong. There was an infinite loop, probably because the template is not properly set up.");
            }
            return $pagesWithoutText;
        }
        return 0;
    }

    /**
    *
    */
    private function CompleteAndWritePDF($pdf)
    {
        // ADD MISSING TEMPLATES
        while($pdf->PageNo() < count($this->templates))
        {
            $headerOnLastPage = $pdf->MyAddPage();
        }

        // ADD REMAINING IMAGES
        while(!empty($this->images))
        {
            // No template for the last pages
            $headerOnLastPage = $pdf->MyAddPage($showTemplate=false);
            // We add one image for each half page
            $width = $pdf->GetWidth();
            $height = $pdf->GetHeight();
            $this->images[0]->InsertIntoPDF($pdf, 0, 0, $width, (int)($height / 2));
            if(isset($this->images[1]))
            {
                $this->images[1]->InsertIntoPDF($pdf, 0, (int)($height / 2), $width, $height);
            }
            array_splice($this->images, 0, 2);
        }
        $pdf->Output();
    }


    /**
    *
    */
	private function ComputeArray($params, $string, $callback) {
	    // No parameter provided, we return an empty array.
	    if(isset($params[$string]) == null)
	    {
	        return array();
	    }

        $param_array = $params[$string];
        if(is_array($param_array))
        {
            // Multiple parameters were given, we add each of them to the out array.
            $result = array();
            foreach ($param_array as $param)
            {
                array_push($result, $callback($param));
            }
            return $result;
        }
        else
        {
            // A single parameter was provided, we return it as a single object array.
            return array($callback($param_array));
        }
	}
}
?>
