using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class class_structures : MonoBehaviour
{
}

[System.Serializable]
public class TcpConfigParameters
{
    public string host;
    public int port;
}

[System.Serializable]
public class JsonCrane
{
    public int totalSegments;
    public int[] totalArmsSegment;
    public int totalArms;
    public bool same_scale;
    public bool same_theta;
    public bool same_material;
    public float phi;
    public float del_phi;
    public JsonCamera camera;
    public DirectionalLight DirectionalLight;
    public int totalPointLights;
    public PointLights[] point_lights;
    public int totalSpotLights;
    public SpotLights[] spot_lights;
    public JsonSegment[] segments;
}

[System.Serializable]
public class SphericalGameObject
{
    public float radius;
    public float theta_deg;
    public float phi_deg;
    public float y_offset;
    public GameObject Object;
    float deg_to_Rad(float deg)
    {
        return 2*Mathf.PI * deg/360;
    }
    public void Update_Pos(float Radius, float Theta, float Phi)
    {
        this.radius = Radius;
        this.theta_deg = Theta;
        this.phi_deg = Phi;
        this.Object.transform.position = new Vector3(
            this.radius * Mathf.Sin(deg_to_Rad(this.theta_deg)) * Mathf.Cos(deg_to_Rad(this.phi_deg)),
            this.radius * Mathf.Cos(deg_to_Rad(this.theta_deg)),
            this.radius * Mathf.Sin(deg_to_Rad(this.theta_deg)) * Mathf.Sin(deg_to_Rad(this.phi_deg)));
        this.Object.transform.rotation = Quaternion.Euler(90-this.theta_deg,-(90+this.phi_deg),0);
    }
    public void Update()
    {
        this.Object.transform.position = new Vector3(
            this.radius * Mathf.Sin(deg_to_Rad(this.theta_deg)) * Mathf.Cos(deg_to_Rad(this.phi_deg)),
            this.radius * Mathf.Cos(deg_to_Rad(this.theta_deg))+this.y_offset,
            this.radius * Mathf.Sin(deg_to_Rad(this.theta_deg)) * Mathf.Sin(deg_to_Rad(this.phi_deg)));
         this.Object.transform.rotation = Quaternion.Euler(90-this.theta_deg,-(90+this.phi_deg),0);
    }
}

[System.Serializable]
public class PointLights : SphericalGameObject
{
    public Vector4 color;
    public float intensity;
    public float range;
}

[System.Serializable]
public class SpotLights : PointLights
{
    public float spot_angle;
}

[System.Serializable]
public class JsonCamera : SphericalGameObject
{
    public int resolution_width;
    public int resolution_height;
    public float FOV;
}

[System.Serializable]
public class DirectionalLight
{
    public float  intensity;
    public float  theta_deg;
}

[System.Serializable]
public class JsonSegment
{
    public float theta_deg;
    public float scale;
    public JsonMaterial material;
}

[System.Serializable]
public class JsonMaterial
{
    public Vector4 color;
    public float metallic;
    public float smoothness;
}