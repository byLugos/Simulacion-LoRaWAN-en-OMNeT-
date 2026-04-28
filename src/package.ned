package wireless3.simulations;

@license(LGPL);

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.inet.StandardHost;
import inet.visualizer.contract.IIntegratedVisualizer;
import inet.node.inet.AdhocHost;

import flora.LoraNode.LoRaNode;
import flora.LoraNode.LoRaGW;
import flora.LoRaPhy.LoRaMedium;

network Wireless3
{
    parameters:
        int numHost;
        double width @unit(m);
        double height @unit(m);
        @display("bgb=$width,$height;bgi=background/mina,s;bgu=m;bgg=50");
    submodules:
        configurator: Ipv4NetworkConfigurator {
            parameters:
                assignDisjunctSubnetAddresses = false;
                @display("p=100,50");
        }

        radioMedium: LoRaMedium {
            @display("p=250,50");
        }

        networkServer: StandardHost {
            parameters:
                @display("p=400,50");
        }

        gateway: LoRaGW {
            @display("p=260,163");
        }

        host[numHost]: LoRaNode {
            @display("i=misc/sensor;p=80,136");
        }

    connections:
        gateway.ethg++ <--> inet.node.ethernet.Eth10M <--> networkServer.ethg++;
}
