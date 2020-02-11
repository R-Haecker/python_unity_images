using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class create_crane : MonoBehaviour
{
    JsonCrane jsonCrane;
    JsonCamera Jcamera;
    public GameObject Cam;
    SphericalGameObject[] PointLights;
    SphericalGameObject[] SpotLights;
    [HideInInspector] public GameObject[] cubes;
    Vector3[] hinges;
    float[] theta_rad_sumed;
    float[] theta_deg_sumed;
    public GameObject TCP_server_object;
    [HideInInspector] public bool newCrane=false;
    [HideInInspector] public bool newPose=false;
    Vector3 rotVec_yz(Vector3 vec,float theta)
    {
        return new Vector3(vec.x,vec.y*Mathf.Cos(theta)-vec.z*Mathf.Sin(theta),vec.y*Mathf.Sin(theta)+vec.z*Mathf.Cos(theta));
    }
    Vector3 rotVec_xz(Vector3 vec,float phi)
    {
        return new Vector3(vec.x*Mathf.Cos(phi)-vec.z*Mathf.Sin(phi),vec.y,vec.x*Mathf.Sin(phi)+vec.z*Mathf.Cos(phi));
    }
    Vector3 rotVec_xy(Vector3 vec,float phi)
    {
        return new Vector3(vec.x*Mathf.Cos(phi)-vec.y*Mathf.Sin(phi),vec.x*Mathf.Sin(phi)+vec.y*Mathf.Cos(phi),vec.z);
    }
    int getTotalAmountofCuboids(int[] total_branches)
    {
        int multi=1;
        int sum = jsonCrane.total_cuboids;
        for (int i=0;i<jsonCrane.total_cuboids-1;i++)
        {
            if(total_branches[i]>1)
            {
                sum = sum + (total_branches[i]*multi-multi)*(jsonCrane.total_cuboids-i-1);
                multi = multi *total_branches[i];
            }
        }
        return sum;
    }
    Vector3 rotVec(Vector3 normal, Vector3 vec, float phi)
    {
        Vector3 norm = normal/Mathf.Sqrt(normal.x*normal.x+normal.y*normal.y+normal.z*normal.z);
        return new Vector3(vec.x*(norm.x*norm.x*(1-Mathf.Cos(phi))+Mathf.Cos(phi))  +  vec.y *(norm.x*norm.y*(1-Mathf.Cos(phi))-norm.z*Mathf.Sin(phi))  + vec.z*(norm.x*norm.z*(1- Mathf.Cos(phi))+norm.y*Mathf.Sin(phi)),
            vec.x*(norm.x*norm.y*(1-Mathf.Cos(phi))+norm.z*Mathf.Sin(phi))  +  vec.y*(norm.y*norm.y*(1-Mathf.Cos(phi))+Mathf.Cos(phi))  +  vec.z*(norm.y*norm.z*(1-Mathf.Cos(phi))-norm.x*Mathf.Sin(phi)),
            vec.x*(norm.x*norm.z*(1-Mathf.Cos(phi))-norm.y*Mathf.Sin(phi))  +  vec.y*(norm.y*norm.z*(1-Mathf.Cos(phi))+norm.x*Mathf.Sin(phi))  +  vec.z*(norm.z*norm.z*(1-Mathf.Cos(phi))+Mathf.Cos(phi)));
    }
    void delete_old_scene()
    {
        //Delete old crane 
        if(cubes!=null)
        {
            for(int i=0; i<cubes.Length;i++)
            {
                Destroy(cubes[i]);
            } 
        }
        if(PointLights!=null)
        {
            for(int i=0; i<PointLights.Length; i++)
            {
                Destroy(PointLights[i].Object);
            }
        }
        if(SpotLights!=null)
        {
            for(int i=0; i<SpotLights.Length; i++)
            {
                Destroy(SpotLights[i].Object);
            }
        }
    }
    void set_minimal_shader()
    {
        if(jsonCrane.request_pose)
        {
            //set shader to unlit i.e. the apperence to minimum
            for (int i = 0; i<getTotalAmountofCuboids(jsonCrane.total_branches); i++)
            {
                Shader shader = Shader.Find("Unlit/Color");
                cubes[i].GetComponent<Renderer>().material.shader = shader;
                Vector4 white_color = new Vector4(1,1,1,1);
                cubes[i].GetComponent<Renderer>().material.color = white_color;
                cubes[i].GetComponent<Renderer>().material.SetFloat("_Metallic", 0);
                cubes[i].GetComponent<Renderer>().material.SetFloat("_Glossiness", 0);
            }
        }
    }
    
    void create_pose()
    {   
        //create enough cubes and hinges
        cubes = new GameObject[getTotalAmountofCuboids(jsonCrane.total_branches)];
        hinges = new Vector3[getTotalAmountofCuboids(jsonCrane.total_branches)];
        string jsondata = JsonUtility.ToJson(jsonCrane);
        Debug.Log("CreateCrane in create_scene; jsondata: " + jsondata);
        UnityEngine.Assertions.Assert.IsTrue(jsonCrane.total_cuboids>0, "The variable total_cuboids from python has to be bigger than zero. total_cuboids: "+ jsonCrane.total_cuboids.ToString());
        if (jsonCrane.total_cuboids==0)
        {
            Debug.LogError("total_cuboids is zero crane can not be created! Check python client.");
            return;
        }
        
        //create Cube-GameObjects, names and set scale of cubes
        for (int i=0; i<getTotalAmountofCuboids(jsonCrane.total_branches); i++)
        {
            Vector3 hinge = new Vector3(0,0,0);
            GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.name = string.Format("Cube_{0}",i);
            if(i<jsonCrane.total_cuboids)
            {
                cube.transform.localScale = new Vector3(1,jsonCrane.cuboids[i].scale,1);
            }
            cubes[i] = cube;
            hinges[i] = hinge;
        }
        
        float max_x = 0;
        float max_y = 0;
        float min_y = 0;

        theta_rad_sumed = new float [jsonCrane.total_cuboids];
        theta_deg_sumed = new float [jsonCrane.total_cuboids];    
        theta_rad_sumed[0] = 0; //jsonCrane.cuboids[0].theta_deg/180 * Mathf.PI;    
        theta_deg_sumed[0] = 0; //jsonCrane.cuboids[0].theta_deg;
        //put the first hinge and cube on the right position
        cubes[0].transform.position = new Vector3(0,0,0);        
        hinges[0] = new Vector3(cubes[0].transform.localScale.x/2,cubes[0].transform.localScale.y/2,0);
        //adjust relative positions of hinges and cubes
        for (int i = 1; i<jsonCrane.total_cuboids; i++)
        {
            theta_rad_sumed[i] = theta_rad_sumed[i-1] + jsonCrane.cuboids[i].theta_deg/180 * Mathf.PI;
            theta_deg_sumed[i] = theta_deg_sumed[i-1] + jsonCrane.cuboids[i].theta_deg;   
            Vector3 del_pos = rotVec_xy(new Vector3(-cubes[i].transform.localScale.x/2, cubes[i].transform.localScale.y/2, 0),-theta_rad_sumed[i]);
            Vector3 del_hinge = rotVec_xy(new Vector3(0,cubes[i].transform.localScale.y,0), -theta_rad_sumed[i]);
            hinges[i] = hinges[i-1] + del_hinge;
            //hinges[i].transform.rotation = Quaternion.Euler(-theta_deg_sumed[i],-jsonCrane.phi,0);
            cubes[i].transform.position = rotVec_xz((hinges[i-1] + del_pos), (jsonCrane.phi)/180 * Mathf.PI);
            cubes[i].transform.rotation = Quaternion.Euler(0,-jsonCrane.phi,-theta_deg_sumed[i]);
        }   
        cubes[0].transform.rotation = Quaternion.Euler(0,-jsonCrane.phi,0);
    }
    void create_branches()
    {
        Vector3 rotAxis = new Vector3();
        int counter = jsonCrane.total_cuboids;
        for (int i = jsonCrane.total_cuboids-2; i>=0;i--)
        {
            if(jsonCrane.total_branches[i]>1)
            {
                int counter_now = counter;
                for(int l=1; l<jsonCrane.total_branches[i];l++)
                {
                    for(int j = i+1; j<counter_now;j++)
                    {   
                        cubes[counter].transform.position = cubes[j].transform.position;
                        cubes[counter].transform.rotation = cubes[j].transform.rotation;
                        cubes[counter].GetComponent<Renderer>().material = cubes[j].GetComponent<Renderer>().material;
                        cubes[counter].transform.localScale = cubes[j].transform.localScale;                       

                        rotAxis = rotVec_xz(rotVec_xy(new Vector3(0,1,0),-theta_rad_sumed[i]),jsonCrane.phi/180 *Mathf.PI);
                        rotAxis = rotAxis.normalized;
                        cubes[counter].transform.RotateAround(cubes[i].transform.position,rotAxis,l*360/jsonCrane.total_branches[i]);    
                        counter = counter +1;
                    }    
                }
            }
        }
    }

    bool is_visible(Camera cam, GameObject[] cubes)
    {

        Plane[] planes = GeometryUtility.CalculateFrustumPlanes(cam);
        foreach (Plane plane in planes) 
        {
            foreach (GameObject cube in cubes)
            {
                foreach (Vector3 vertice in cube.GetComponent<MeshFilter>().mesh.vertices) 
                {
                    if(plane.GetDistanceToPoint(cube.transform.position + vertice) < 1)
                    {
                        return false;
                    }
                }
            }
        }
        return true;
    }
    bool create_camera()
    {
        Jcamera = new JsonCamera();
        Jcamera.Object = Cam;
        Debug.Log("camera.radius: " + jsonCrane.camera.radius.ToString());    
        Jcamera.theta_deg = jsonCrane.camera.theta_deg;
        Jcamera.phi_deg = jsonCrane.camera.phi_deg;
        Camera.main.fieldOfView = jsonCrane.camera.FOV;
        Jcamera.Update();
        if(jsonCrane.camera.radius==-1)
        {
            return false;
        }
        else
        {
            Jcamera.radius = jsonCrane.camera.radius;
            Jcamera.Update();
            return true;
        }
        
    }

    void create_apperence()
    {
        PointLights = new SphericalGameObject[jsonCrane.totalPointLights];
        SpotLights = new SphericalGameObject[jsonCrane.totalSpotLights];

        //adjust Directional Light
        Transform DLight_Transform;
        DLight_Transform = GetComponent<Transform>();
        DLight_Transform.rotation = Quaternion.Euler(90 - jsonCrane.DirectionalLight.theta_deg,0,0);
        Light lt;
        lt = GetComponent<Light>();
        lt.intensity = jsonCrane.DirectionalLight.intensity;

        //create pointlights and set properties
        for (int i = 0; i<jsonCrane.totalPointLights; i++)
        {
            PointLights[i] = new SphericalGameObject();
            PointLights[i].radius = jsonCrane.point_lights[i].radius;
            PointLights[i].theta_deg = jsonCrane.point_lights[i].theta_deg;
            PointLights[i].phi_deg = jsonCrane.point_lights[i].phi_deg;
            
            GameObject lightGameObject = new GameObject();
            lightGameObject.name = string.Format("PointLight_{0}",i);
            Light lightComp = lightGameObject.AddComponent<Light>();
            lightComp.shadows= LightShadows.Soft;
            lightComp.type = LightType.Point;
            lightComp.color = jsonCrane.point_lights[i].color;
            lightComp.intensity =  jsonCrane.point_lights[i].intensity;
            lightComp.range = jsonCrane.point_lights[i].range;
            PointLights[i].Object = lightGameObject;
            PointLights[i].Update();    
        }
        //create Spotlights and set properties
        for (int i = 0; i<jsonCrane.totalSpotLights; i++)
        {
            SpotLights[i] = new SphericalGameObject();
            SpotLights[i].radius = jsonCrane.spot_lights[i].radius;
            SpotLights[i].theta_deg = jsonCrane.spot_lights[i].theta_deg;
            SpotLights[i].phi_deg = jsonCrane.spot_lights[i].phi_deg;
            
            GameObject lightGameObject = new GameObject();
            lightGameObject.name = string.Format("SpotLight_{0}",i);
            Light lightComp = lightGameObject.AddComponent<Light>();
            lightComp.shadows= LightShadows.Soft;
            lightComp.type = LightType.Spot;
            lightComp.color = jsonCrane.spot_lights[i].color;
            lightComp.intensity =  jsonCrane.spot_lights[i].intensity;
            lightComp.range = jsonCrane.spot_lights[i].range;
            lightComp.spotAngle = jsonCrane.spot_lights[i].spot_angle;
            SpotLights[i].Object = lightGameObject;
            SpotLights[i].Update();    
        }
        
        //adjust Material color
        for (int i = 0; i<jsonCrane.total_cuboids; i++)
        {
            Shader shader = Shader.Find("Custom/standard_shader");
            cubes[i].GetComponent<Renderer>().material.shader = shader;
            cubes[i].GetComponent<Renderer>().material.color = jsonCrane.cuboids[i%jsonCrane.total_cuboids].material.color;
            cubes[i].GetComponent<Renderer>().material.SetFloat("_Metallic", jsonCrane.cuboids[i%jsonCrane.total_cuboids].material.metallic);
            cubes[i].GetComponent<Renderer>().material.SetFloat("_Glossiness", jsonCrane.cuboids[i%jsonCrane.total_cuboids].material.smoothness);
        }
    }

    void Update()
    {
        if(TCP_server_object.GetComponent<TCP_server>().ready_to_build)
        {   
            Debug.Log("CreateCrane in Update: before creating any scene: import ready_to_build == true;");
            //load json data from TCP_server script   
            jsonCrane = TCP_server_object.GetComponent<TCP_server>().jsonCrane_here;
            if(jsonCrane.request_pose && (!TCP_server_object.GetComponent<TCP_server>().image_sent))
            {
                Debug.Log("CreateCrane in Update: request_pose == true and import image_sent == false;");
                Debug.Log("CreateCrane in Update: Now deleting old crane and creating new one;");
                delete_old_scene();
                create_pose();
                create_apperence();
                create_branches();
                if(!create_camera())
                {
                    Debug.Log("Calculating radius for the camera;");
                    while(!is_visible(Cam.GetComponent<Camera>(), cubes))
                    {
                        Jcamera.radius = Jcamera.radius + 1;
                        Jcamera.Update();
                    }
                    Debug.Log("Radius set to: " + Jcamera.radius.ToString());        
                }
                newCrane = true;
                Debug.Log("CreateCrane in Update: Crane created; newCrane == true;");
            }
            if(jsonCrane.request_pose && TCP_server_object.GetComponent<TCP_server>().image_sent)
            {
                Debug.Log("CreateCrane in Update: request_pose == true and import image_sent == true;");
                Debug.Log("CreateCrane in Update: Now creating pose;");
                set_minimal_shader();
                newPose=true;
                Debug.Log("CreateCrane in Update: Pose created;");
            }

            if(!(jsonCrane.request_pose) && (!TCP_server_object.GetComponent<TCP_server>().image_sent))
            {
                Debug.Log("CreateCrane in Update: request_pose == false and import image_sent == false;");
                delete_old_scene();
                create_pose();
                create_apperence();
                create_branches();
                if(!create_camera())
                {
                    Debug.Log("Calculating radius for the camera;");
                    //Jcamera.Update();
                    while(!is_visible(Cam.GetComponent<Camera>(), cubes))
                    {
                        Debug.Log("Update Radius:");
                        Jcamera.radius = Jcamera.radius + 1;
                        Jcamera.Update();
                    }
                    Debug.Log("Radius set to: " + Jcamera.radius.ToString());
                }
                newCrane = true;
                Debug.Log("CreateCrane in Update: Crane created;");
            }
        }
    }

}
