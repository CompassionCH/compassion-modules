## -*- coding: utf-8 -*-
<html>
<head>
  <title>mako compassion template </title>
  <style type="text/css">
          #main_div {
              position:absolute;
              width:21cm;
          }

          #child_infos {
              position:absolute;
              height:10.3cm;
              width:21cm;
          }

          #child_picture_ {
              position:absolute;
              height:10.2cm;
              text-align:left;
          }

          #child_desc_up {
              position:absolute;
              top:0cm;
              left:7.5cm;
              width:9cm;
          }

          #child_square_img_ {
              position:absolute;
              top:0cm;
              left:9.4cm;
              width:1.9cm;
          }

          #child_desc_work {
              position:absolute;
              top:4.5cm;
              left:7.5cm;
              height:5.7cm;
              width:11.4cm;
          }

          #tab_separator_{
              position:absolute;
              top:11cm;
              left:0cm;
              width:21cm;
          }

          #write_maj {
              position:absolute;
              top:14.5cm;
              left:0cm;
              width:21cm;
              text-align:center;
          }

          #sponsor_form {
              position:absolute;
              top:16.5cm;
              left:0cm;
              height:10cm;
              width:21cm;
          }

          #policy {
              position:absolute;
              left:0cm;
              width:9cm;
          }

          #sponsor_infos {
              position:absolute;
              left:9.5cm;
              width:9cm;
          }

          #newsletter {
              position:absolute;
              top:26.5cm;
              left:0cm;
              width:21cm;
          }

          #mail_infos {
              position:absolute;
              top:27.5cm;
              left:0cm;
              height:2cm;
              width:21cm;
              text-align:center;
          }

          #region_infos {
              position:absolute;
              top:32cm;
              left:0cm;
              height:7.5cm;
              width:21cm;
          }

          #region_img_ {
              position:absolute;
              left:0cm;
              height:6.8cm;
              width:9cm;
          }

          #project_desc_1 {
              position:absolute;
              top:0cm;
              left:10cm;
              height:7.5cm;
              width:9cm;
          }

          #project_desc_2 {
              position:absolute;
              top:39.5cm;
              left:0cm;
              height:3.5cm;
              width:21cm;
          }

          #compassion_infos {
              position:absolute;
              top:43.5cm;
              right:0cm;
              height:2.5cm;
              width:7cm;
          }

          ul{
          list-style-type: none;
          padding: 0;
          margin-left: 0;
          }

  </style>
</head>
<body>
    <div id="main_div" width=100% border="1">
        <!-- CHILD INFORMATION -->
        <div id="child_infos" class="child_infos" >
            <div id="child_picture" class="child_picture" >
              <img src="data:image/png;base64,[...base64 here...]" />
              <!--<img src="img/BF6830018.jpg" id="child_picture_" />-->
            </div>
            <div id="child_desc" class="child_desc">
                <div id="child_desc_up" class="child_desc_up">
                    <div id="child_desc_names" class="child_desc_names">
                        <p>Name: ${child_name}</li>
                        <ul>
                        <li>Country: ${child_birthdate}</li>
                        <li>Birthdate: ${project_country}</li>
                        <li>Child Ref.: ${child_code}</li>
                        <li>Project center: ${project_name}</li>
                        </ul>
                    </div>
                    <div id="child_square_img" class="child_desc_img">
                        <img src="data:image/png;base64,[...base64 here...]" />
                        <!--<img src="img/blue_corner_rough.jpg" id="child_square_img_" />-->
                    </div>
                </div>
                <div id="child_desc_work" class="child_desc_work">
                    ${child_desc}
                </div>
            </div>
        </div>
        <!-- TAB IMAGE SEPARATOR -->
        <div id="tab_separator" class="tab_separator">
            <img src="data:image/png;base64,[...base64 here...]" />
            <!--<img src="img/LogoCompassion_baseline_url_compassion.ch_2000x206px.png" id="tab_separator_" />-->
        </div>
        <div id="write_maj" class="write_maj">
            <ul>
                <li>${write_maj}</li>
                <li>${child_ref}</li>
            </ul>
        </div>
        <!-- SPONSOR FORM  -->
        <div id="sponsor_form" class="sponsor_form">
            <div id="policy" class="policy">
                ${sponsor_plan}
            </div>
            <div id="sponsor_infos" class="sponsor_infos">
                ${sponsor_infos}
            </div>
        </div>
        <div id="newsletter" class="newsletter">
            <!--<input type="checkbox" name="receive_infos" value="Milk"> I want to receive informations...-->
            ${newsletter}
        </div>
        <div id="mail_infos" class="mail_infos">
            ${mail_infos}
        </div>
        <!-- REGION INFOS -->
        <div id="region_infos" class="region_infos">
            <div id="region_img" class="region_img">
                <img src="data:image/png;base64,[...base64 here...]" />
                <!--<img src="img/map_of_burkina-faso.jpg" id="region_img_" />-->
            </div>
            <div id="project_desc_1" class="project_desc_1">
            ${project_desc}
            </div>
        </div>
        <div id="project_desc_2" class="project_desc_2">
            Project code: ${project_code}
        </div>
        <!-- COMPASSION INFOS -->
        <div id="compassion_infos" class="compassion_infos">
            ${compassion_infos}
        </div>
    </div>
</body>
</html>
