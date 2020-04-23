using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class lock_fps : MonoBehaviour
{
    public int target = 30;         
    void Awake()
    {
        //disable audio 
        AudioListener audioListener = GetComponent<AudioListener>(); 
        audioListener.enabled = false;
        //lock framerate
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = target;
    }
}