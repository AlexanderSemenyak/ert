/*
   Copyright (C) 2011  Equinor ASA, Norway.

   The file 'obs_data.h' is part of ERT - Ensemble based Reservoir Tool.

   ERT is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   ERT is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.

   See the GNU General Public License at <http://www.gnu.org/licenses/gpl.html>
   for more details.
*/

#ifndef ERT_OBS_DATA_H
#define ERT_OBS_DATA_H
#ifdef __cplusplus
extern "C" {
#endif
#include <stdio.h>
#include <stdbool.h>

#include <ert/util/hash.h>
#include <ert/util/rng.h>

#include <ert/res_util/matrix.hpp>
#include <ert/enkf/enkf_types.hpp>
#include <ert/enkf/meas_data.hpp>

typedef struct obs_data_struct   obs_data_type;
typedef struct obs_block_struct  obs_block_type;
void         obs_block_free( obs_block_type * obs_block );
active_type  obs_block_iget_active_mode( const obs_block_type * obs_block , int iobs);
obs_block_type * obs_block_alloc( const char * obs_key , int obs_size , matrix_type * error_covar , bool error_covar_owner, double global_std_scaling);
int obs_block_get_active_size( const obs_block_type * obs_block );

void         obs_block_deactivate( obs_block_type * obs_block , int iobs , bool verbose , const char * msg);
int          obs_block_get_size( const obs_block_type * obs_block );
void         obs_block_iset( obs_block_type * obs_block , int iobs , double value , double std);
void         obs_block_iset_missing( obs_block_type * obs_block , int iobs );

double obs_block_iget_std( const obs_block_type * obs_block , int iobs);
double obs_block_iget_value( const obs_block_type * obs_block , int iobs);
bool   obs_block_iget_active( const obs_block_type * obs_block , int iobs);

const char * obs_data_iget_keyword( const obs_data_type * obs_data , int index );
double       obs_data_iget_value( const obs_data_type * obs_data , int index );
double       obs_data_iget_std( const obs_data_type * obs_data, int i_ndex );
active_type  obs_data_iget_active_mode( const obs_data_type * obs_data , int index );
obs_block_type       * obs_data_iget_block( obs_data_type * obs_data , int index );
const obs_block_type *     obs_data_iget_block_const( const obs_data_type * obs_data , int block_nr);
obs_block_type *     obs_data_get_block( obs_data_type * obs_data , const char * obs_key );
obs_block_type *     obs_data_add_block( obs_data_type * obs_data , const char * obs_key , int obs_size , matrix_type * error_covar , bool error_covar_owner);
void obs_data_scale_matrix(const obs_data_type * obs_data , matrix_type * matrix);
void obs_data_scale_Rmatrix(const obs_data_type * obs_data , matrix_type * matrix);

obs_data_type      * obs_data_alloc(double global_std_scaling);
void                 obs_data_free(obs_data_type *);
void                 obs_data_reset(obs_data_type * obs_data);
matrix_type        * obs_data_allocD(const obs_data_type * obs_data , const matrix_type * E  , const matrix_type * S);
matrix_type        * obs_data_allocR(const obs_data_type * obs_data );
matrix_type        * obs_data_allocdObs(const obs_data_type * obs_data );
matrix_type        * obs_data_allocE(const obs_data_type * obs_data , rng_type * rng , int active_ens_size);
  void                 obs_data_scale(const obs_data_type * obs_data , matrix_type *S , matrix_type *E , matrix_type *D , matrix_type *R , matrix_type * O);
void                 obs_data_iget_value_std(const obs_data_type * obs_data , int index , double * value ,  double * std);
int                  obs_data_get_active_size(const obs_data_type * obs_data );
int                  obs_data_get_total_size( const obs_data_type * obs_data );
int                  obs_data_get_num_blocks( const obs_data_type * obs_data );
const char * obs_block_get_key( const obs_block_type * obs_block) ;
double       obs_data_iget_value( const obs_data_type * obs_data , int total_index );
double       obs_data_iget_std( const obs_data_type * obs_data , int total_index );

const bool_vector_type * obs_data_get_active_mask( const obs_data_type * obs_data );

#ifdef __cplusplus
}
#endif
#endif
