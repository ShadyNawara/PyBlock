The main part of this project is a python plugin that would allow beginner developers to implement a data log and transfer between multiple nodes and sensors using a block chain with as little as 3 lines of code. The pyblock plugin contains 2 main classes: a Client and a Node. A client would typically be a sensor that needs to log its data. the node(s) are the ones processing transactions or mines it in blockchain terms. This helps make a wireless sensor environment insusceptible to many types of hacking or data manipulation common to today's most used process of using a central server. The implementation also offers a great level of redundancy that the system would remain functioning for as long as at least one node is active. For testing I am using a dragonboard 410 attached to a temperature sensor. I then run multiple nodes on my laptop. The dragonboard sends temperature readings frequently to any random node. I can then display a graph of the acquired temperatures over time

To start a client

`from pyblock import Client
bClient = Client(nodes, 'private key', 'public key')
bClient.send("Temperature = Cold!!!")`

To Start a node

`import pyblock
node = pyblock.Initialize(['other nodes urls'], port)`
I built the main plugin by taking inspiration from various online resources and tutorials and of course all references are mentioned on the website i made as a landing page for the project. The way the plugin works makes it different from any other block chain algorithm or plugin as its main focus is allowing the ease of use and being lightweight enough for compact IOT devices and sensors

One of the main challenges i ran into was trying to setup the dragonboard and a raspberry pi that i use for testing through the wifi here. Also, I am pretty new to blockchain in general so, working with it has been a real challenge

I managed to get my plugin to work at super fast speed between a raspberry pi, dragonboard and my laptop

I have learned a lot about blockchain technology and how to work with a dragonboard as i am pretty new to both

What's next for PyBlock: I will be experimenting with different encryption algorithms trying to find the best match between security and speed. I will also be changing the way i currently process communications between nodes as i am currently using a simple flask http server
