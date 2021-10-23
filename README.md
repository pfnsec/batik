Batik is a Python framework for simplifying dataflow programming.

It's basically a bunch of glue code for connecting steps in a data pipeline,
with support for stateful actors, multithreading, and model serving.

Hot-reload sort of works too, but I'm still ironing out the kinks.

I wrote Batik because I hated having to screw around with initializing threads, queues, 
handling IPC, and having to decipher just what a data science or signal processing 
pipeline was doing from a giant block of imperative code.

In Batik, you implement processing steps, or layers, on their own,
and stitch them together in batik.yaml, for an approach more resembling gnuradio or simulink without the gui. 


Terminology:

Manifest: The complete setup of what to run/serve. Read from batik.yaml.

Layer: A single processing step in a pipeline. Takes some data as a parameter, 
operates on it, and returns some data.

Endpoint: A sequence of one or more layers. Used as an api endpoint for model serving.
May be invoked dynamically from other layers to do things like fan-out based on value etc.

Actor: A stateful class, initialized at runtime. The methods of the class may be 
used as layers or daemons.

Daemon: A generator function that runs at startup. Each generated value is passed to a 
specified endpoint, possibly through some layers.

See examples for more.

Batik is kind of a mess at the moment. If you want to contribute, I'll buy you a beer.