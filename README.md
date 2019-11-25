# Movies-ETL

### Project Overview : ### 

An automate process is created for Extratin , trasnsforming and loading the data source. In this process data will be collected from three different sources: </br>

**1.** Wikipedia Data : This is  in Jason format. Containg the information about the movies  <BR>
**2.** Kaggle Metadata: File downloaded from the Kaggle Website ,it has details like title, director and other information related      to a movie <BR>
**3.**  Ratings : CSV file downloaded fomr kaggle website , it has rating for all the movoes<BR> 
  
### Process:  </br>

The information from all the three sources are taken togther and merged into one movies_df which is then loaded to the databases . To do this following steps are taken . <BR>
**1.** Transform : The raw data is converted into the suitable form .all the duplicarte and null values are removed .</br>
**2.** Merge : The datasets made through step 1 ae them merged togther using inner and left join to get the required resuls</br>
**3.** Load : The result is then uploaded to a table movies which is created a database in post grates.</br>

 A sequntial process (funtion) is created  for autaomaing the process and while creating this various try and black statments are used to catch any error alont the way. <br>



### Assumptions: </br>
**1.** Even though data cleansing and integration is done on the raw data, the data can be further cleansed which is left behind because of the time contraints  only data which effect the result in greater percentage is considered. </br>
**2.** While creating the process instead of the incremental process , full load method is used where in we ae assuming if table is already there . Full load method is easy to maintain and code , but it is very time consuming and take more CPU space a compared to the incremental load.</br>
**3.** Once data is loaded in the tables no further data quality test are done to check if the data is loaded properly , just a couunt query is performed to see the right number of rows are prsent the data sets . </br>


 
