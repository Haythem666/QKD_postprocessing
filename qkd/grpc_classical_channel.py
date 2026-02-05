"""
gRPC Classical Channel
Allows Bob to communicate with Alice over the network.
"""

import grpc
import sys
import os

# Add qkd directory to path to import pb2 files
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    import qkd_grpc_cascade_pb2
    import qkd_grpc_cascade_pb2_grpc
except ImportError as e:
    print(f"ERROR: gRPC files not found! {e}")
    print("Run: python -m grpc_tools.protoc -I. --python_out=qkd --grpc_python_out=qkd qkd_grpc_cascade.proto")
    sys.exit(1)


class gRPCClassicalChannel:
    """
    Classical communication channel via gRPC.
    Bob uses this channel to request parities from Alice.
    """
    
    def __init__(self, server_address='localhost:50051'):
        """
        Args:
            server_address (str): Alice server address (e.g. 'localhost:50051')
        """
        self.server_address = server_address
        self.bits_leaked = 0
        
        # Create connection to Alice server
        self.channel = grpc.insecure_channel(server_address)
        self.stub = qkd_grpc_cascade_pb2_grpc.CascadeServiceStub(self.channel)
        
        print(f"[Bob] Connected to Alice at {server_address}")
    
    def start_reconciliation(self, algorithm_name):
        """Signal to Alice the start of reconciliation"""
        request = qkd_grpc_cascade_pb2.StartRequest(algorithm_name=algorithm_name)
        try:
            self.stub.StartReconciliation(request)
            print(f"[Bob] Started reconciliation with {algorithm_name}")
        except grpc.RpcError as e:
            print(f"[Bob] ERROR: Cannot reach Alice - {e}")
            raise
    
    def ask_parities(self, blocks):
        """
        Request parities of multiple blocks from Alice.
        
        Args:
            blocks (list): List of Block objects
            
        Returns:
            list: List of parities (0 or 1)
        """
        # Convert Block objects to protobuf messages
        block_infos = []
        for block in blocks:
            block_info = qkd_grpc_cascade_pb2.BlockInfo(
                shuffle_id=str(block.get_shuffle().get_identifier()),
                start_index=block.get_start_index(),
                end_index=block.get_end_index()
            )
            block_infos.append(block_info)
        
        # Create the request
        request = qkd_grpc_cascade_pb2.ParityRequest(blocks=block_infos)
        
        # Send to Alice and receive response
        try:
            response = self.stub.AskParities(request)
            parities = list(response.parities)
            
            self.bits_leaked += len(parities)
            print(f"[Bob] Received {len(parities)} parities from Alice (total leaked: {self.bits_leaked})")
            
            return parities
            
        except grpc.RpcError as e:
            print(f"[Bob] ERROR: Communication with Alice failed - {e}")
            raise
    
    def end_reconciliation(self, algorithm_name):
        """Signal to Alice the end of reconciliation"""
        request = qkd_grpc_cascade_pb2.EndRequest(algorithm_name=algorithm_name)
        try:
            self.stub.EndReconciliation(request)
            print(f"[Bob] Ended reconciliation")
        except grpc.RpcError as e:
            print(f"[Bob] WARNING: Could not notify Alice of end - {e}")
    
    def close(self):
        """Close the connection"""
        self.channel.close()
        print("[Bob] Closed connection to Alice")