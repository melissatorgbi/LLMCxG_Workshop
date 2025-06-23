class TestTemplates :
    def __init__( self ) :

        self.test_templates    = {

            'named_selector_example_lrec' : {
                'style' : 'ChatCompletion' ,
                'version': 'v2',
                'use_example' : True,
                'zero' : """From amongst the following sentences, extract the three sentences which are instances of the {} construction, as exemplified in the following sentence: "{}" Output only the three sentences in three separate lines: 
{},
{},
{},
{},
{},
{},
Answer:""", 
                'one' : """From amongst the following sentences, extract the three sentences which are instances of the {} construction, as exemplified in the following sentence: "{}" Output only the three sentences in three separate lines: 
{},
{},
{},
{},
{},
{},
Answer:{};
From amongst the following sentences, extract the three sentences which are instances of the {} construction, as exemplified in the following sentence: "{}" Output only the three sentences in three separate lines: 
{},
{},
{},
{},
{},
{},
Answer:""",
                },
            
            'named_selector_example_lrec_exemplar' : { ## Exactly the same as named_selector_example_lrec
                'style' : 'ChatCompletion' ,
                'version': 'v2',
                'use_example' : True,
                'zero' : """From amongst the following sentences, extract the three sentences which are instances of the {} construction, as exemplified by the following sentence: "{}" Output only the three sentences in three separate lines: 
{},
{},
{},
{},
{},
{},
Answer:""", 
                'one' : """From amongst the following sentences, extract the three sentences which are instances of the {} construction, as exemplified by the following sentence: "{}" Output only the three sentences in three separate lines: 
{},
{},
{},
{},
{},
{},
Answer:{};
From amongst the following sentences, extract the three sentences which are instances of the {} construction, as exemplified by the following sentence: "{}" Output only the three sentences in three separate lines: 
{},
{},
{},
{},
{},
{},
Answer:""",
                },
            
}
