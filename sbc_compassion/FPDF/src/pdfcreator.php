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

const SEE_ATTACHMENT = array(
    "fr_CH" => "Voir la traduction ci-jointe",
    "de_DE" => "Siehe beiliegende Uebersetzung",
    "it_IT" => "Vedi traduzione allegata",
    "en_US" => "See attached translation"
);
const Translation = array(
    "fr_CH" => "Traduction",
    "de_DE" => "Uebersetzung",
    "it_IT" => "Traduzione",
    "en_US" => "Translation"
);

class PDFCreator
{
	protected $images;              // Array of images                          => array[Image]
	protected $texts;               // Array of the text zones                  => array[Text]
	protected $utils;               // Utilities that provides useful functions => TemplateUtils
    protected $originalSize;        // Indicates the original number of pages PDF => Int
    protected $lang;                // The lang of the output => string

	protected $headerOnLastPage;

	protected $preventOverflow;     // If set to true, we don't allow boxes to overflow and insert directly a special
                                    // template page holding overflown text. Otherwise, the text will naturally spread
                                    // through the available boxes.
	protected $overflowPage;        // Will be set when overflow occurs. Holds the overflown texts from the current page.  => array[Text]

    /**
    *
    */
    function __construct($params)
    {
        $templates = $this->ComputeArray($params, 'templates', function($template)
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

        $this->lang = $params['lang'];
        $overflowTemplate = false;
        if (!empty($params['overflow_template'])) {
            $overflowTemplate = new Template(...$params['overflow_template']);
            $this->preventOverflow = $params['prevent_overflow'];
        }
        $this->originalSize = $params['original_size'];


        // We don't accept PDFs with no template.
        if(count($templates) == 0)
        {
            throw new Exception("No templates provided, cannot generate PDF");
        }
        $this->utils = new TemplateUtils($templates, $params['original_size'], $overflowTemplate);
        $headerOnLastPage = false;
        $this->overflowPage = [];
    }


    /**
    *
    */
    function createPDF($pdf_name)
    {
        // SET UP
        $pdf = new MyFPDF($this->utils);
        $pdf->AddFont('Montserrat','R','montserrat.php');
        $pdf->SetFont('Montserrat', 'R', 12);

        $consecutiveEmptyPages = 0;
        // CREATE NEW PAGE AND FILL IT WITH CONTENT
        while (!empty($this->texts))
        {
	        $headerOnLastPage = $pdf->MyAddPage();
            $template = $this->utils->GetTemplateForPageNo($pdf->PageNo());

	        $emptyPage = $this->InsertText($pdf, $template, $this->preventOverflow);

	        // Insert additional page only on front pages
	        if (!empty($this->overflowPage) && $pdf->PageNo() % 2 == 0) {
	            $this->InsertOverflowPages($pdf);
            }

	        $this->InsertImages($pdf, $template);

	        $consecutiveEmptyPages = $this->PreventInfiniteLoop($pdf, $emptyPage, $consecutiveEmptyPages);
        }

        // COMPLETE THE END OF THE PDF AND WRITE IT
        $this->CompleteAndWritePDF($pdf, $pdf_name);
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
    private function InsertText($pdf, $template, $preventOverflow)
    {
        $emptyPage = true;
        $toRemove = [];
        for ($i = 0; $i < count($this->texts); $i++) {
            // Find the first box matching the text type.
            $text = $this->texts[$i];
            foreach ($template->GetTextBoxes() as $textBox) {
                if($text->HasType($textBox->GetType()) && $textBox->Available()) {
                    $emptyPage = false;
                    $textBox->Use();
                    $remainingText = $pdf->MyMultiCell($textBox->GetMinX(), $textBox->GetMinY(), $textBox->GetMaxX(), $textBox->GetMaxY(), $text->GetText(), $height=$textBox->GetHeight(), $preventOverflow);
                    if($remainingText != "") {
                        // An overflow occurred
                        if ($preventOverflow) {
                            array_push($this->overflowPage, $text->GetText());
                            array_push($toRemove, $i);
                            $pdf->MyMultiCell($textBox->GetMinX(), $textBox->GetMinY(), $textBox->GetMaxX(), $textBox->GetMaxY(), (SEE_ATTACHMENT[$this->lang] ?? SEE_ATTACHMENT["en_US"]) . " #" . count($this->overflowPage), $height=$textBox->GetHeight());
                        } else {
                            // The text was still printing in the box, we put the remaining text in the following boxes
                            $text->SetText($remainingText);
                        }
                    } else {
                        array_push($toRemove, $i);
                    }
                    break;
                }
            }
        }
        // Remove empty texts from the list of texts that must be handled
        foreach (array_reverse($toRemove) as $i) {
            array_splice($this->texts, $i, 1);
        }
        return $emptyPage;
    }

    private function InsertOverflowPages($pdf) {
        $template = $this->utils->overflowTemplate;
        $text = "";
        for ($i=1; $i <= count($this->overflowPage); $i++) {
            $text = $text . (Translation[$this->lang] ?? Translation["en_US"]) . " #" .$i . ": \n\n" . $this->overflowPage[$i-1] . "\n\n";
        }
        while ($text != "") {
            // Add an extra page with overflow template
            $this->utils->addExtraPage($pdf->PageNo());
            $pdf->MyAddPage();
            // Fill all text boxes
            foreach ($template->GetTextBoxes() as $textBox) {
                $text = $pdf->MyMultiCell($textBox->GetMinX(), $textBox->GetMinY(), $textBox->GetMaxX(), $textBox->GetMaxY(), $text, $height = $textBox->GetHeight());
            }
        }
        $this->overflowPage = [];
    }


    /**
    *
    */
    private function PreventInfiniteLoop($pdf, $emptyPage, $pagesWithoutText)
    {
        if($emptyPage)
        {
            $pagesWithoutText++;
            if($pagesWithoutText >= 4) {
                if ($this->utils->overflowTemplate) {
                    // Try to push remaining text on overflow page
                    $this->InsertOverflowPages($pdf);
                } else {
                    throw new Exception("Could not generate PDF, something went wrong. There was an infinite loop, probably because the template is not properly set up.");
                }
            }
            if($pagesWithoutText >= 6) {
                // Force throwing exception if looping increase even after inserting overflow pages
                throw new Exception("Could not generate PDF, something went wrong. There was an infinite loop, probably because the template is not properly set up.");
            }
            return $pagesWithoutText;
        }
        return 0;
    }

    /**
    *
    */
    private function CompleteAndWritePDF($pdf, $pdf_name)
    {
        // ADD Missing overflows (if we can insert a FRONT page)
        if (!empty($this->overflowPage) && $pdf->PageNo() % 2 == 0) {
            while (!empty($this->overflowPage)) {
                $this->InsertOverflowPages($pdf);
            }
        }

        // ADD MISSING TEMPLATES
        while($pdf->PageNo() < count($this->utils->templates))
        {
            $headerOnLastPage = $pdf->MyAddPage();
            $this->InsertImages($pdf, $this->utils->GetTemplateForPageNo($pdf->PageNo()));
        }

        // Add remaining overflow (in case we didn't have a FRONT page prior to remaining template pages)
        while (!empty($this->overflowPage)) {
            $this->InsertOverflowPages($pdf);
        }

        // ADD REMAINING IMAGES
        while(!empty($this->images))
        {
            // No template for the last pages
            $headerOnLastPage = $pdf->MyAddPage($showTemplate=false);
            // We add one image for each half page
            $width = $pdf->GetWidth();
            $height = $pdf->GetHeight();
            $yMin = 10;

            // If the height permits it, we put two pictures on the same page. Otherwise we put them in separate pages
            $fullPage = true;
            $image = $this->images[0];
            if ($image->height <= $height/2) {
                $height = (int)($height / 2);
                $fullPage = false;
            }
            $this->images[0]->InsertIntoPDF($pdf, 10, $yMin, $width-10, $height-10);
            if(isset($this->images[1])) {
                if ($fullPage) {
                    $pdf->MyAddPage($showTemplate=false);
                } else {
                    $yMin = $height;
                }
                $this->images[1]->InsertIntoPDF($pdf, 10, $yMin, $width-10, $pdf->GetHeight()-10);
            }
            array_splice($this->images, 0, 2);
        }
        $pdf->Output("F", $pdf_name);
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
