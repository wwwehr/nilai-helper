```mermaid
sequenceDiagram
    title healthcare-3-doctor-mccoy.py

    participant Agent as Local CDP Agent
    participant Server as nilAI Server
    participant nilDB as nilSecretVault

    Note over Agent,nilDB: CREATE DIAGNOSIS PRIVATE INFERENCE
    rect rgba(0, 255, 0, .1)
        Agent->>Server: Create medical diagnosis from chart

        activate Server  
            Note over Server: [reasoning]
            Server->>Server: Perform inference
            Server->>Agent: Return final inference result
        deactivate Server

    end

    Note over Agent,nilDB: SAVE TO SECUREVAULT TOOL
    rect rgba(0, 0, 255, .1)
        Agent->>Server: Lookup schema
        activate Server  
            Note over Server: [worker]        
            Server->>Server: Perform inference
            Server->>Agent: Return response with tool call detected
            activate Agent
                Agent->>Agent: execute tool
                Agent->>nilDB: Get all schema definitions
                nilDB->>Agent: Return all schema definitions
                Agent->>Server: Send updated context with tool results
            deactivate Agent
            Server->>Server: Perform inference (select schema)
            Server->>Agent: schema definition
        deactivate Server

        Agent->>Server: Save to SecureVault prompt
        Server->>Agent: Return response with tool call detected


        activate Agent  
            Note over Server: [worker]
            Agent->>Server: Transform output to schema format
            Server->>Agent: Transformed data set
            Agent->>nilDB: Save to SecureVault
            nilDB->>Agent: Return ids
        deactivate Agent
    end
```
