import logging
import os
from typing import Annotated, Optional

import vtk

import numpy as np
from __main__ import qt, slicer
import math
import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode


#
# MeasurementWithSpheres
#


class MeasurementWithSpheres(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("MeasurementWithSpheres")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#MeasurementWithSpheres">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        
       
        # Additional initialization step after application startup is complete
 

 
#
# MeasurementWithSpheresParameterNode
#


@parameterNodeWrapper
class MeasurementWithSpheresParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """
    lineNode = vtk.vtkLineSource()
    tube = vtk.vtkTubeFilter()
    tube2 = vtk.vtkTubeFilter()
    tube3 = vtk.vtkTubeFilter()
    modelsLogic = slicer.modules.models.logic()

    lineNode2 =  vtk.vtkLineSource()
    lineNode3 =  vtk.vtkLineSource()
    angleNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsAngleNode','Angle')
# Get markup node from scene
    markups = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLMarkupsFiducialNode')
    i=0
    count=1
    spheres = [vtk.vtkSphereSource() for _ in range(4)]
    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100

    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode
    lineLength: Annotated[float, WithinRange(0, 300)] = 50
    center0:float
    radius0:float
    center1:float
    radius1:float
    center2:float
    radius2:float
    center3:float
    radius3:float




#
# MeasurementWithSpheresWidget
#


class MeasurementWithSpheresWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/MeasurementWithSpheres.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        
        
        
       
        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)
        
        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = MeasurementWithSpheresLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)

        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.ui.createangle.connect("clicked(bool)", self.createAngle)
        self.ui.changeangleposition.connect("clicked(bool)", self.changeAnglePosition)
        self.ui.generateline.connect("clicked(bool)", self.generateLine)
        self.ui.deleteline.connect("clicked(bool)", self.deleteLine)


        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()



    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[MeasurementWithSpheresParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
            self.ui.applyButton.toolTip = _("Compute output volume")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input and output volume nodes")
            self.ui.applyButton.enabled = False
    def deleteLine(self)->None:
        name=self.ui.linetobedeleted.toPlainText()
        self.logic.deleteLine(name)
    def generateLine(self)->None:
        coordinates = self.ui.coordinatesofline.toPlainText().split(',')

 
        x, y, z = map(int, coordinates)
        
       
        self.logic.generateLine(self.ui.lineLengthSliderWidget.value,x,y,z, self.ui.nameofline.toPlainText())

    def changePoints(self,markups,spheres, caller=None, event=None)->None:
       
         
        
        
        self.logic.UpdateModels(self._parameterNode.lineNode,self._parameterNode.lineNode2,self._parameterNode.lineNode3,self._parameterNode.angleNode,self._parameterNode.i,self._parameterNode.count,self._parameterNode.markups,self._parameterNode.spheres,self._parameterNode.tube,self._parameterNode.tube2,self._parameterNode.tube3)

    def createAngle(self, caller=None, event=None)->None:
        for itemIndex, sphere in enumerate(self._parameterNode.spheres):
            sphere.SetPhiResolution(30)
            sphere.SetThetaResolution(30)
            model =self._parameterNode.modelsLogic.AddModel(sphere.GetOutputPort())
            model.GetDisplayNode().SetVisibility2D(True)
            model.GetDisplayNode().SetSliceIntersectionThickness(3)
            model.GetDisplayNode().SetColor(1,1-itemIndex*0.3,itemIndex*0.3)
    
        if self._parameterNode.angleNode is None:
            
            self._parameterNode.lineNode =  vtk.vtkLineSource()
            self._parameterNode.lineNode2 =  vtk.vtkLineSource()
            self._parameterNode.lineNode3 = vtk.vtkLineSource()
            self._parameterNode.angleNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsAngleNode','Angle')
                # Get markup node from scene
            self._parameterNode.markups = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLMarkupsFiducialNode')
            self._parameterNode.i=0
            self._parameterNode.count=1
        self.logic.UpdateModels(self._parameterNode.lineNode,self._parameterNode.lineNode2,self._parameterNode.lineNode3,self._parameterNode.angleNode,self._parameterNode.i,self._parameterNode.count,self._parameterNode.markups,self._parameterNode.spheres,self._parameterNode.tube,self._parameterNode.tube2,self._parameterNode.tube3,self._parameterNode.modelsLogic)
        self._parameterNode.markups.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.changePoints, 2)

    def changeAnglePosition(self)->None:
        self._parameterNode.i, self._parameterNode.count = self.logic.changeAngle(
        self._parameterNode.i,
        self._parameterNode.count,
        self._parameterNode.angleNode,
        self._parameterNode.markups
    )   


        
    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            

            # Compute output
            self.logic.process(self._parameterNode.lineNode,self._parameterNode.lineNode2,self._parameterNode.lineNode3,self._parameterNode.angleNode,self._parameterNode.i,self._parameterNode.count,self._parameterNode.markups,self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)


#
# MeasurementWithSpheresLogic
#


class MeasurementWithSpheresLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        

    def getParameterNode(self):
        return MeasurementWithSpheresParameterNode(super().getParameterNode())
    
    def deleteLine(self,name):
        deletedline = slicer.util.getNode(name)
        deletedline.RemoveAllControlPoints()
    def generateLine(self,lineLength,x,y,z,nameofline):
        lineNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode', nameofline)
        lineNode.AddControlPointWorld(x,y,z)
        
        lineNode.AddControlPointWorld(x,y,z+lineLength)
        lineDisplayNode = slicer.util.getNode(lineNode.GetDisplayNodeID())
       
        # Set line color (red in this example)
        lineDisplayNode.SetColor([1, 0, 0])

        # Set line thickness
        lineDisplayNode.SetLineWidth(2)
       

    def sphereFrom3Points(self,markupsNode, startPointIndex):
        """Compute center and radius of 3-point sphere from 3 fiducial points
        source: https://stackoverflow.com/questions/20314306/find-arc-circle-equation-given-three-points-in-space-3d
        """
        A = np.zeros(3)
        B = np.zeros(3)
        C = np.zeros(3)
        if markupsNode is None:
            markupsNode=slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLMarkupsFiducialNode')
        markupsNode.GetNthControlPointPosition(startPointIndex,A)
        markupsNode.GetNthControlPointPosition(startPointIndex+1,B)
        markupsNode.GetNthControlPointPosition(startPointIndex+2,C)
        a = np.linalg.norm(C - B)
        b = np.linalg.norm(C - A)
        c = np.linalg.norm(B - A)
        s = (a + b + c) / 2
        R = a*b*c / 4 / np.sqrt(s * (s - a) * (s - b) * (s - c))
        b1 = a*a * (b*b + c*c - a*a)
        b2 = b*b * (a*a + c*c - b*b)
        b3 = c*c * (a*a + b*b - c*c)
        P = np.column_stack((A, B, C)).dot(np.hstack((b1, b2, b3)))
        P /= b1 + b2 + b3
        return P, R

    def UpdateModels(self,lineNode,lineNode2,lineNode3,angleNode,i,count,markups,spheres,tube,tube2,tube3,modelsLogic):
        """Update the sphere and line models from the fiducial points"""
        
        center0, radius0 = self.sphereFrom3Points(markups,0)
        center1, radius1 = self.sphereFrom3Points(markups, 3)
        center2, radius2 = self.sphereFrom3Points(markups, 6)

        center3, radius3 = self.sphereFrom3Points(markups, 9)

        

        spheres[0].SetCenter(center0)
        spheres[0].SetRadius(radius0)
        spheres[1].SetCenter(center1)
        spheres[1].SetRadius(radius1)
        spheres[2].SetCenter(center2)
        spheres[2].SetRadius(radius2)
        spheres[3].SetCenter(center3)
        spheres[3].SetRadius(radius3)

        
        
        
      
        

        lineNode.SetPoint1(center0)
        lineNode.SetPoint2(center1)

        lineNode2.SetPoint1(center2)
        lineNode2.SetPoint2(center3)

        tube.SetInputConnection(lineNode.GetOutputPort())
        model = modelsLogic.AddModel(tube.GetOutputPort())
        model.GetDisplayNode().SetVisibility2D(True)
        model.GetDisplayNode().SetSliceIntersectionThickness(2)
        model.GetDisplayNode().SetColor(1, 0.4, 0.6)

        tube2.SetInputConnection(lineNode2.GetOutputPort())
        model2 = modelsLogic.AddModel(tube2.GetOutputPort())
        model2.GetDisplayNode().SetVisibility2D(True)
        model2.GetDisplayNode().SetSliceIntersectionThickness(2)
        model2.GetDisplayNode().SetColor(1, 0.4, 0.6)


        
    
    # Update line endpoints
    
    
        
        
        
        
        
        
        
        
        
        # Calculate the midpoint between the centers of Sphere 1 and Sphere 2
        midpoint_1_2 = (center0 + center1) / 2

        # Calculate the midpoint between the centers of Sphere 3 and Sphere 4
        midpoint_3_4 = (center2 + center3) / 2
        
        tube3.SetInputConnection(lineNode3.GetOutputPort())
        model3 = modelsLogic.AddModel(tube3.GetOutputPort())
        model3.GetDisplayNode().SetVisibility2D(True)
        model3.GetDisplayNode().SetSliceIntersectionThickness(2)
        model3.GetDisplayNode().SetColor(1, 0.4, 0.6)
        angleNode.RemoveAllControlPoints()
        angleNode.AddControlPointWorld(midpoint_1_2)     
        angleNode.AddControlPointWorld(midpoint_3_4)
        
        

        angleDisplayNode = slicer.util.getNode(angleNode.GetDisplayNodeID())

        # Set line color (red in this example)
        angleDisplayNode.SetColor([1, 0, 0])
        distance_anglepoints = np.linalg.norm(midpoint_3_4 - midpoint_1_2)

         
        print('distance between layers is:',distance_anglepoints)
    
        # Set line thickness
        angleDisplayNode.SetLineWidth(2)

        
        tube.Modified()
        tube2.Modified()
        tube3.Modified()

        slicer.util.forceRenderAllViews()


    def changeAngle(self,i,count,angleNode,markups):

         
        centertemp=0
     
        if i<4 :
            if i!=0:
                angleNode.RemoveNthControlPoint(2)
            
            center, radius = self.sphereFrom3Points(markups, i*3)
            centertemp=center
            angleNode.AddControlPointWorld(center)
            count=+1
            i+=1
        else:
            i=0
            positionofangle0= angleNode.GetNthControlPointPosition(0)
            positionofangle1= angleNode.GetNthControlPointPosition(1)
            center, radius = self.sphereFrom3Points(markups, 0)
            angleNode.RemoveAllControlPoints()
            angleNode.AddControlPointWorld(positionofangle1)
            angleNode.AddControlPointWorld(positionofangle0)
        return i, count

     

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """
        
        


        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")


#
# MeasurementWithSpheresTest
#


class MeasurementWithSpheresTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_MeasurementWithSpheres1()
'''
    def test_MeasurementWithSpheres1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        inputVolume = SampleData.downloadSample("MeasurementWithSpheres1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = MeasurementWithSpheresLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
'''