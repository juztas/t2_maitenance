#!/usr/bin/perl -w
# $Id: glexec_unwrapenv.pl,v 1.1 2012/04/02 16:09:31 asciaba Exp $
#
# Helper script to restore the environment variables previously
# wrapped into the environment variable GLEXEC_ENV using the
# glexec_wrapenv.pl script. 
#
# Intended usage:
#   export GLEXEC_ENV=`glexec_wrapenv.pl`
#   /opt/glite/sbin/glexec glexec_unwrapenv.pl -- <YOUR-COMMAND>
#
# By default the following environment variables are NOT unwrapped:
#   HOME LOGNAME USER X509_USER_PROXY _  (yes that's '_' !)
# A user can add more env vars to be excluded using either
#  --exclude=A --exclude=B
# or
#  --exclude=A,B,...
#
# Copyright (c) 2009 by
#   Jan Just Keijser (janjust@nikhef.nl)
#   Nikhef
#   Amsterdam
#   The Netherlands

use strict;
use warnings;

use Compress::Zlib qw(inflateInit Z_STREAM_END Z_OK);
use Getopt::Long   qw(GetOptions);
use MIME::Base64   qw(decode_base64);

# These variables are excluded by default
my @env_blacklist = ( "HOME", "LOGNAME", "USER", "X509_USER_PROXY", "_" );
my @exclude_env;

GetOptions ("exclude=s" => \@exclude_env);
@exclude_env = split( /,/, join( ',', @exclude_env, @env_blacklist) );

$ENV{GLEXEC_ENV} 
    or die "GLEXEC_ENV not set. No environment to pass on";

# First, unwrap the Base64 encoded blob
my $decoded_buf = decode_base64( $ENV{GLEXEC_ENV} );

# Then, decompress it into it's original space-separated set of Base64 blobs
my $x = inflateInit()
    or die "Cannot create a inflation stream\n" ;

my ($output, $status) = $x->inflate( \$decoded_buf );

die "inflation failed\n"
    unless $status == Z_STREAM_END or $status == Z_OK;

# Split the space-separated set of Base64 blobs again into an array
my @vars = split / /, $output;

for (my $i = 0; $i <= $#vars; $i++)
{
    # Decode each Base64 encoded blob into a key=value pair
    my $keyvalue_pair = decode_base64( $vars[$i] );
    my $pos = -1;

    # Look for the first '=' sign
    if (($pos = index( $keyvalue_pair, '=' )) > -1 )
    {
        # NOTE: using tricks like (\w+) (\w+) will NOT work
        # when environment variables span multiple lines

        # the "key" is everything before the first '=' sign
        my $key   = substr( $keyvalue_pair, 0, $pos );
        # the "value" is everything after the first '=' sign
        my $value = substr( $keyvalue_pair, $pos+1 );

        # if the variable is not on our exclusion list, set it
        if ( ! grep { /$key/ } @exclude_env )
        {
            $ENV{$key} = $value;
        }
    }
    else
    {
        # this should never happen, really
        printf STDERR  "no = sign found in [$keyvalue_pair]!\n";
    }
}

# Finally, execute the user payload command
exec ( @ARGV );

