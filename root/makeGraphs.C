#include "CMSSW_BASE_REPLACETAG/CSCValidation/root/cscValFunctions.C"

void makeGraphs(TString inputdir = ".", int maxfiles = 300) {

  TChain* rhchain = new TChain("recHits/rHPositions");
  TChain* segchain = new TChain("Segments/segPositions");

  int nfiles = rhchain->Add(inputdir+"/valHists_*.root");
  cout << "[makeGraphs] Total number of files: " << nfiles << endl;
  segchain->Add(inputdir+"/valHists_run*.root");

  //Make global position graphs from trees
  GlobalPosfromChain("Global recHit positions ME+1", rhchain, 1, 1, "rechit", "rHglobal_station_+1.png");
  GlobalPosfromChain("Global recHit positions ME+2", rhchain, 1, 2, "rechit", "rHglobal_station_+2.png");
  GlobalPosfromChain("Global recHit positions ME+3", rhchain, 1, 3, "rechit", "rHglobal_station_+3.png");
  GlobalPosfromChain("Global recHit positions ME+4", rhchain, 1, 4, "rechit", "rHglobal_station_+4.png");
  GlobalPosfromChain("Global recHit positions ME-1", rhchain, 2, 1, "rechit", "rHglobal_station_-1.png");
  GlobalPosfromChain("Global recHit positions ME-2", rhchain, 2, 2, "rechit", "rHglobal_station_-2.png");
  GlobalPosfromChain("Global recHit positions ME-3", rhchain, 2, 3, "rechit", "rHglobal_station_-3.png");
  GlobalPosfromChain("Global recHit positions ME-4", rhchain, 2, 4, "rechit", "rHglobal_station_-4.png");
  GlobalPosfromChain("Global Segment positions ME+1", segchain, 1, 1, "segment", "Sglobal_station_+1.png");
  GlobalPosfromChain("Global Segment positions ME+2", segchain, 1, 2, "segment", "Sglobal_station_+2.png");
  GlobalPosfromChain("Global Segment positions ME+3", segchain, 1, 3, "segment", "Sglobal_station_+3.png");
  GlobalPosfromChain("Global Segment positions ME+4", segchain, 1, 4, "segment", "Sglobal_station_+4.png");
  GlobalPosfromChain("Global Segment positions ME-1", segchain, 2, 1, "segment", "Sglobal_station_-1.png");
  GlobalPosfromChain("Global Segment positions ME-2", segchain, 2, 2, "segment", "Sglobal_station_-2.png");
  GlobalPosfromChain("Global Segment positions ME-3", segchain, 2, 3, "segment", "Sglobal_station_-3.png");
  GlobalPosfromChain("Global Segment positions ME-4", segchain, 2, 4, "segment", "Sglobal_station_-4.png");

}
