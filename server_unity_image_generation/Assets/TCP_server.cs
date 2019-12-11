using System;
using System.Collections;
using System.Collections.Generic;
using System.Threading;
using System.Net;
using UnityEngine;
using System.Net.Sockets;
using System.Text;
using System.IO;
//using System.Windows.Forms;

public class TCP_server : MonoBehaviour
{
    public GameObject create_crane_object;
    Thread tcpListenerThread;
    TcpListener server = null;
    TcpClient client;
    string jsonparameters;
    TcpConfigParameters TcpConfig;
    NetworkStream stream;
    [HideInInspector] public JsonCrane jsonCrane_here;
    [HideInInspector] public bool ready_to_build = false;
    bool client_accepted = false;
    bool running_session = true;
    string file_path_data_unity;
    [HideInInspector] public float timer = 0.0f;
       
    // Use this for initialization
	void Start () 
    {   
        Screen.fullScreen = false;
        Screen.SetResolution(1, 1, false);
        tcpListenerThread = new Thread(() => ListenForMessages());
        tcpListenerThread.Start();
        if (Application.isEditor)
        {
            file_path_data_unity = System.IO.Directory.GetParent(System.Environment.CurrentDirectory).ToString() + "/data/unity/";        
        
        }
        else
        {
            file_path_data_unity = System.Environment.CurrentDirectory.ToString() + "/data/unity/";        
        }
        System.IO.File.WriteAllText(file_path_data_unity + "started.txt", "1");
	}
	
	// Update is called once per frame
	void LateUpdate() 
    {
        timer += Time.deltaTime;
        if(client_accepted == false && timer > 30.0f)
        {
            Debug.Log("TCP_Server in LateUpdate: TIMEOUT reached now stopping server." + Time.realtimeSinceStartup.ToString());
            running_session = false;
        }
        if(!running_session)
        {
            Debug.Log("TCP_Server in LateUpdate: running_session == false; now closing Unity.");
            System.IO.File.WriteAllText(file_path_data_unity + "started.txt", "0");
            Application.Quit();
        }
        if(create_crane_object.GetComponent<create_crane>().newCrane)
        {
            Debug.Log("TCP_Server in LateUpdate: before CapturePNGasBytes: import newCrane == true;");
            Debug.Log("TCP_Server in LateUpdate: before CapturePNGasBytes: Time: " + Time.realtimeSinceStartup.ToString());
            timer =0;
            StartCoroutine(CapturePNGasBytes());
            ready_to_build=false;
            Debug.Log("TCP_Server in LateUpdate: after CapturePNGasBytes:  ready_to_build==false; import newCrane == true;");
            Debug.Log("TCP_Server in LateUpdate: after CapturePNGasBytes: Time: " + Time.realtimeSinceStartup.ToString());
        }
    }
    private IEnumerator CapturePNGasBytes()
    {
        yield return new WaitForEndOfFrame();
        Camera currentCamera = GetComponent<Camera>();
        if(jsonCrane_here.camera.soild_background)
        {
            currentCamera.clearFlags = CameraClearFlags.SolidColor;
        } 
        //create RenderTexture and Texture2D
        RenderTexture rt = new RenderTexture(jsonCrane_here.camera.resolution_width, jsonCrane_here.camera.resolution_height, 24, RenderTextureFormat.ARGB32);
        Texture2D sceneTexture = new Texture2D(jsonCrane_here.camera.resolution_width, jsonCrane_here.camera.resolution_height, TextureFormat.RGB24, false);
        
        currentCamera.targetTexture = rt;
        currentCamera.Render();
        RenderTexture.active = rt;
        sceneTexture.ReadPixels(new Rect(0,0,jsonCrane_here.camera.resolution_width,jsonCrane_here.camera.resolution_height),0,0);
        sceneTexture.Apply();
        //clean up
        currentCamera.targetTexture = null;
        RenderTexture.active = null;
        
        byte[] bytesPNG = sceneTexture.EncodeToPNG();
        byte[] MessageEndTag = {125,99,255,255,255,255,255,255};
        Destroy(sceneTexture);
        Debug.Log("TCP_Server in CapturePNGasBytes: bytesPNG.Length: " + bytesPNG.Length.ToString());
        Debug.Log("TCP_Server in CapturePNGasBytes: sending PNG bytes: ");
        try
        {
            Debug.Log("TCP_Server in CapturePNGasBytes: try: stream.CanWrite");
            stream = client.GetStream();
            if (stream.CanWrite)
            {
                Debug.Log("TCP_Server in CapturePNGasBytes: stream.CanWrite==true");
                // Write byte array to socketConnection stream.
                stream.Write(bytesPNG, 0, bytesPNG.Length);
                // Write End Tag to stream
                stream.Write(MessageEndTag, 0, MessageEndTag.Length);
                Debug.Log("TCP_Server in CapturePNGasBytes: message sent - picture should be received by client");
            }
        }
        catch (SocketException socketException)
        {
            Debug.Log("TCP_Server in CapturePNGasBytes: Socket exception: " + socketException);
        }
        ready_to_build = false;
    }

    public void ListenForMessages()
    {
        // use for non server build option:
        //only for server
        string jsontcpconfig = File.ReadAllText(file_path_data_unity + "server_tcp_config.json");
        TcpConfig = JsonUtility.FromJson<TcpConfigParameters>(jsontcpconfig);
        Debug.Log("TCP_Server in ListenForMessages: TCPconfig loaded");
        System.Net.IPAddress localAddr = System.Net.IPAddress.Parse(TcpConfig.host);
        Debug.Log("TCP_Server in ListenForMessages: IPAdress: " + localAddr.ToString() + "; port: " + TcpConfig.port);
        server = new TcpListener(localAddr, TcpConfig.port);

        // Start listening for client requests.
        server.Start();

        // Buffer for reading data
        Byte[] bytes = new Byte[1048576];
        String data = null;
        
        client = server.AcceptTcpClient();
        client_accepted = true;
        // Enter the listening loop.
        Debug.Log("TCP_Server in ListenForMessages: Waiting for a connection... ");
        
        Debug.Log("TCP_Server in ListenForMessages: Connected at: "+client.ToString());
        while(running_session)
        {
            // if there is a change request it should come in the next 3 minutes
            if(timer>=20.0f)
            {
                Debug.Log("TCP_Server in ListenForMessages: change_req was true but nothing came for 3 minutes; closing listening thread");
                running_session=false;
            }
            Debug.Log("TCP_Server in ListenForMessages: in nested while(true): Connected at: "+client.ToString());
            // Get a stream object for reading and writing
            stream = client.GetStream();

            Debug.Log("TCP_Server in ListenForMessages: waiting for stream.Read()");
            // Loop to receive all the data sent by the client.
            data = null;
            int i=0;
            while ((i = stream.Read(bytes, 0, bytes.Length)) != 0)
            {   
                // Translate data bytes to a ASCII string.
                data = System.Text.Encoding.ASCII.GetString(bytes, 0, i);
                Debug.Log("TCP_Server in ListenforMessages: Received data");
                if(data.Substring(data.Length - 4) =="eod.")
                {
                    Debug.Log("TCP_Server in ListenForMessages: eod. detected");
                    if (data.Substring(data.Length - 8) == "END.eod.")
                    {
                        Debug.Log("TCP_Server in ListenForMessages: END.eod. detected");
                        Debug.Log("TCP_Server in ListenForMessages: set: server.Stop(); running_session==false");
                        running_session = false;
                        server.Stop();
                        return;
                    }
                    else
                    {
                        jsonparameters = data.Substring(0,data.Length - 4);
                        Debug.Log("TCP_Server in ListenForMessages: jsonparameters: "+ jsonparameters);
                        this.jsonCrane_here = JsonUtility.FromJson<JsonCrane>(jsonparameters);
                        if(this.jsonCrane_here.total_cuboids!=0)
                        {
                            ready_to_build=true;
                            Debug.Log("TCP_Server in ListenForMessages: ready_to_build == true");
                        }
                        else
                        {
                            Debug.Log("ERROR: Loaded JsonCrane data but total_cuboids==0 aborting.");
                        }
                        break;
                    }
            
                }
            }
        }
    }
}