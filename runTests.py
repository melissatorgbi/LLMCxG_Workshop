import re
import os
import csv
import sys
import copy
import pickle
import openai
from openai import OpenAI

from tqdm          import tqdm
from TestTemplates import TestTemplates

class runTests :

    def __init__( self, data_location, output_location, openai_completion_style, test_data_version=None,  OPENAI_API_KEY=None) :
        
        self.output_location         = output_location
        self.openai_completion_style = openai_completion_style
        self.OPENAI_API_KEY = OPENAI_API_KEY
        
        self.cxgs = [ "Let Alone", "Way Manner", "Resultative","Conative","Intransitive Motion", "Caused Motion", "Causative with CxN", "Ditransitive CxN", "Comparative Correlative", "Much Less" ]
        self.cxgs = [ i.rstrip().lstrip() for i in self.cxgs ]


        self.test_data         = self._load_test_data( data_location, test_data_version )
        
        #self._load_openai_key()

        tt = TestTemplates()
        self.test_templates = tt.test_templates

        self.exemplars = { 
            "Let Alone" : 	"None of these arguments is notably strong, let alone conclusive.",
            "Way Manner" : 	"A middle-aged man eased his way into the room." , 
            "Resultative" : 	"Firefighters cut the man free." , 
            "Conative" :	"She kicked at the ball." ,
            "Intransitive Motion" :	"The fly buzzed into the room." ,
            "Caused Motion" :	"They laughed the actor off the stage." ,
            "Causative with CxN" : 	"She loaded the truck with books." ,
            "Ditransitive CxN"	: "She baked her sister a cake.",
            "Comparative Correlative" : 	"The more I studied, the less I understood",
            "Much Less" : 	"He has not yet been put on trial much less found guilty.",
        }

        return 

    def _load_test_data( self, data_location, test_data_version ) :
        test_data_file = os.path.join( data_location, 'test_data.pk3' )
        if not test_data_version is None :
            test_data_file  = os.path.join( data_location, 'test_data_version_{}.pk3'.format( test_data_version ) )
        print( "Loading test data: ", test_data_file ) 
        with open( test_data_file, 'rb' ) as fh :
            return pickle.load( fh )
        return
    
    def _load_openai_key( self ) :
        with open( '.key' ) as fh :
            data = fh.readlines()
            self.org_key, self.user_key = data[0].split( ',' )
        openai.organization = self.org_key
        openai.api_key = self.user_key
        return

    def get_exemplar( self, cxg ) :
        return self.exemplars[ cxg ]
    
    def _generate_prompt_lrec( self, cxg, example_data, template_name, setting, exemplar=None ) :

        if not exemplar is None : 
            example_data = copy.deepcopy( example_data )
            for e_id in [0,1] :
                old_exemplar = example_data[ e_id ][2]
                for i in range( 6 ) :
                    if example_data[e_id][0][i] == exemplar :
                        example_data[e_id][0][i] = old_exemplar
                example_data[e_id][2] = exemplar

            

        ## Must be version 2 style prompt
        assert self.test_templates[ template_name ]['version'] == 'v2'
        
        prompt = None
        if setting == 'zero' :
            if not self.test_templates[ template_name ][ 'use_example' ] : 
                prompt = self.test_templates[ template_name ][ 'zero' ].format(
                    cxg, 
                    example_data[0][0][0], example_data[0][0][1], example_data[0][0][2],
                    example_data[0][0][3], example_data[0][0][4], example_data[0][0][5]
                )
            else : # use example
                prompt = self.test_templates[ template_name ][ 'zero' ].format(
                    cxg,
                    example_data[0][2],
                    example_data[0][0][0], example_data[0][0][1], example_data[0][0][2],
                    example_data[0][0][3], example_data[0][0][4], example_data[0][0][5]
                )
        elif setting == 'one' :

            target = list()
            for target_id in example_data[1][1] :
                target.append( example_data[1][0][ target_id ] )
            target = '\n'.join( target ) 
            
            if not self.test_templates[ template_name ][ 'use_example' ] :
                prompt = self.test_templates[ template_name ][ 'one' ].format(
                    cxg,
                    example_data[1][0][0], example_data[1][0][1], example_data[1][0][2],
                    example_data[1][0][3], example_data[1][0][4], example_data[1][0][5],
                    target,
                    cxg,
                    example_data[0][0][0], example_data[0][0][1], example_data[0][0][2],
                    example_data[0][0][3], example_data[0][0][4], example_data[0][0][5]
                )
            else : # use example
                prompt = self.test_templates[ template_name ][ 'one' ].format(
                    cxg,
                    example_data[1][2],
                    example_data[1][0][0], example_data[1][0][1], example_data[1][0][2],
                    example_data[1][0][3], example_data[1][0][4], example_data[1][0][5],
                    target,
                    cxg,
                    example_data[0][2],
                    example_data[0][0][0], example_data[0][0][1], example_data[0][0][2],
                    example_data[0][0][3], example_data[0][0][4], example_data[0][0][5]
                )
        else :
            raise Exception( "Unknown setting" ) 

        return prompt

    

    def _cached_get( self, model, template_name, setting, cxg, example_id, prompt ) :
        response = {}
        cache_path      = os.path.join( self.output_location, model, template_name, setting, cxg )
        cache_file      =  '{}.pk3'.format( example_id )
        cache_file_path = os.path.join( cache_path, cache_file )
        if os.path.exists( cache_file_path ) :
            with open( cache_file_path, 'rb' ) as fh :
                return pickle.load( fh )
        if not os.path.exists( cache_path ) :
            os.makedirs( cache_path )

        if self.openai_completion_style == 'ChatCompletion' :
            
            client = OpenAI(api_key=self.OPENAI_API_KEY)

            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                    ]
                    )
            output = completion.choices[0].message.content

            response[ 'prompt' ] = prompt
            response[ 'answer' ] = output
        
        with open( cache_file_path, 'wb' ) as fh :
            pickle.dump( response, fh )
            
        return response
        

    def _score_exact_match_v2( self, response_answer, target ) :
        response_set = set( [ re.sub( r'\s*,\s*$', '', i ) for i in response_answer.split( '\n' ) ] )
        target_set   = set( target )
        return len( target_set - response_set ) == 0

    def _score_relaxed_match_v2( self, response_answer, target ):
        responses = [ re.sub( r'\s*,\s*$', '', i.lower() ) for i in response_answer.split( '\n' ) ]
        targets   = [ i.lower() for i in target ]
        contained = 0
        for single_target in targets :
            for single_response in responses :
                if single_response == '' :
                    continue
                if (single_response in single_target) or (single_target in single_response) :
                    contained += 1
                    continue
        return (contained/3)
        

    def test_cxg_v2( self, model, template_name, setting, cxg, test_number=None, prompt_generator='default' ) :

        print( "Testing {} on template {} in the {}-shot setting, on the CXG {}".format( model, template_name, setting, cxg ) )
        
        this_cxg_test_data = self.test_data[ cxg ]
        if test_number is None :
            test_number = len( this_cxg_test_data ) 
        scores_exact     = list()
        scores_relaxed   = list()
        responses        = list()
        for example_id in tqdm( range( test_number ) ) :
            prompt   = None
            if prompt_generator == 'lrec' :
                this_exemplar = None
                if '_exemplar' in template_name :
                    this_exemplar = self.get_exemplar( cxg )
                prompt   = self._generate_prompt_lrec( cxg, this_cxg_test_data[ example_id ], template_name, setting, exemplar=this_exemplar )
            else :
                raise Exception( "Unknown prompt generator" ) 
                
            response = self._cached_get( model, template_name, setting, cxg, example_id, prompt )
            if self.openai_completion_style == 'Completion' :
                if not 'answer' in response :
                    response[ 'answer' ] = response['message']['content']
            target = list()
            for target_id in this_cxg_test_data[ example_id ][0][1] :
                target.append( this_cxg_test_data[ example_id ][0][0][ target_id ] )

            response[ 'target' ] = target
            response_answer = response[ 'answer' ]
            scores_exact.    append( self._score_exact_match_v2  ( response_answer, target ) )
            scores_relaxed.  append( self._score_relaxed_match_v2( response_answer, target ) ) ## Actual number
            responses.append( response )
            
           

        ## Write output
        exact_accuracy     = (scores_exact    .count( True ) / len( scores_exact     ) ) * 100
        relaxed_accuracy   = ( sum( scores_relaxed ) / len( scores_relaxed   ) ) * 100

        score_path = os.path.join( self.output_location, model, template_name, setting, cxg )
        if not os.path.exists( score_path ) :
            os.makedirs( score_path )
        outstring = "Exact accuracy:{}\nRelaxed accuracy:{}".format( exact_accuracy, relaxed_accuracy )
        with open( os.path.join( score_path, 'scores_{}.txt'.format( test_number ) ), 'w' ) as fh :
            fh.write( outstring )

        print( "{}\t{}".format( round( exact_accuracy, 2 ), round( relaxed_accuracy, 2 ) ) )

        errors = [ [ "Prompt", "Target", "Model Output", "Exact Match", "Relaxed Match" ] ]
        for example_id in range( test_number ) :
            row = [responses[ example_id ] ['prompt'], responses[ example_id ] ['target'], responses[ example_id ]['answer'], str( scores_exact[ example_id ] ), str( scores_relaxed[ example_id ] ) ]
            errors.append( row )
        errors_file = os.path.join( score_path, 'errors_{}.csv'.format( test_number ) )
        with open( errors_file, 'w' ) as fh :
            csv_writter = csv.writer( fh )
            csv_writter.writerows( errors )
        print( "Wrote outputs to: ", errors_file )
        return

    def test_all_cxgs( self, model, template_name, settings, test_version=1, prompt_generator='default' ) :
        for cxg in self.cxgs : 
            for setting in settings :
                if test_version == 2 :
                    self.test_cxg_v2( model, template_name, setting, cxg, prompt_generator=prompt_generator )
            break   
        return
    

if __name__ == '__main__' :
    openai_completion_style = 'ChatCompletion'
    tester = runTests( 'CxGData', 'output', openai_completion_style, test_data_version='lrec' )
    tester.test_all_cxgs( 'gpt-4o-mini', 'named_selector_example_lrec_exemplar', [ 'zero', 'one' ], test_version=2, prompt_generator='lrec' )

    
