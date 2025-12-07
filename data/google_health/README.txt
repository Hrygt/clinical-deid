Labels for Physionet Gold Corpus following the I2B2-2014 de-identification challenge guidelines
===============================================================================================

The data consists of labels for the Physionet Gold Corpus dataset:
  https://physionet.org/content/deidentifiedmedicaltext/1.0/.

Annotation follows the guidelines described in section 4 of:
  Amber Stubbs OU. Annotating longitudinal clinical narratives for de-identification: the 2014
  i2b2/UTHealth Corpus. J Biomed Inform. 2015;58(Suppl):S20,
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4978170/.

This labeling was used in the paper "Customization Scenarios for De-identification of Clinical
Notes" in order to generate results for models trained on I2B2-2014 dataset, and evaluated on the
Physionet Gold Corpus dataset.

Contact:
-------
For questions or comments, please contact corresponding authors appearing in the paper.

Data:
----
Data includes:

1. I2B2-2014-Relabeled-PhysionetGoldCorpus.csv Comma Separated Values with the following columns:
a. record_id - string of the form "<int>||||<int>||||" corresponding to the id given in the original Physionet Gold Corpus dataset.
   For example, "22||||35||||" corresponds to START_OF_RECORD=22||||35|||| start marker in the original Physionet corpus.
b. begin - int, specifying the relative offset of the span relative to START_OF_RECORD.
c. length - int, specifying the length of span.
d. type - enum, with one of the following values: NAME, AGE, ORGANIZATION, ID, DATE, CITY, STATE, COUNTRY, LOCATION, HOSPITAL, PHONE, PROFESSION.
