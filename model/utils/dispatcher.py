import copy
import importlib
import math
import model.utils.dijakstra as dijakstra
import model.utils.dispatcher_utils as dispatcher_utils
from model.entities.vertex import Vertex
from model.entities.point import Point

def run_algorithm_on_world(world,alg_name,tpd):
  vertexes = create_vertexes_from_visit_points(world)
  algo = import_algorithm(alg_name)
  patrol = start_patrol(world,algo,tpd,vertexes)
  return {
    'world': world,
    'patrol': patrol,
  }

def create_vertexes_from_visit_points(world):
  return [Vertex(vp['probability'],vp['starvation'],vp['position']) for vp in world['visit_points']]

def import_algorithm(alg_name):
  try:
    algo_module = importlib.import_module('model.algs.{}'.format(alg_name))
    return getattr(algo_module,alg_name.capitalize())
  except ModuleNotFoundError:
    raise NameError("the algorithm: '{}' doesn't exist!".format(alg_name))

def start_patrol(world,algo,tpd,vertexes):
  distance_matrix = create_distance_matrix(world)
  global_time = 0
  robot = {
    'position': vertexes[world['robot']['start_point']].point,
    'current_vertex': world['robot']['start_point'],
    'angle': world['robot']['start_angle'],
    'walk_speed': world['robot']['walk_speed'],
    'rotation_speed': world['robot']['rotation_speed'],
  }
  patrol = []
  while global_time < tpd:
    next_vertex = algo.next_step(robot['current_vertex'],vertexes, distance_matrix,global_time)
    frames_of_path = path_to_goal(robot, world, next_vertex)
    robot['current_vertex'] = next_vertex
    global_time += len(frames_of_path)
    vertexes[next_vertex].visit(global_time)
    patrol.append(frames_of_path)
  
  return patrol

def path_to_goal(robot, world, next_vertex):
  return complex_path_steps(world,robot['current_vertex'],next_vertex)

def create_distance_matrix(world):
  vps = world['visit_points']
  matrix = [[0] * len(vps)] * len(vps)
  for i,_ in enumerate(vps):
    for j,_ in enumerate(vps):
      matrix[i][j] = complex_path_length(world,i,j)
  return matrix

def complex_path_length(world,vp_src,vp_dst):
  return len(complex_path_steps(world,vp_src,vp_dst))

def complex_path_steps(world,vp_src,vp_dst):
  path = dijakstra.get_points_path_with_dijakstra(world,world['visit_points'][vp_src]['position'],world['visit_points'][vp_dst]['position'])
  frames = []
  if len(path) == 1:
    return [{'angle': 0, 'position': path[0]}]
  for i in range(0, len(path) - 1):
    frames += simple_path_steps(path[i], path[i + 1], world['robot']['walk_speed'], world['robot']['rotation_speed'])
  return frames

def simple_path_steps(p_src, p_dst,walk_speed,rotation_speed):
  frames = []
  target_angle = dispatcher_utils.calculate_new_angle(p_src,p_dst)
  frames = dispatcher_utils.get_rotation_frames(target_angle,p_src,rotation_speed)
  total_distance = int(math.sqrt(((p_dst.x - p_src.x)**2) + ((p_dst.y - p_src.y)**2)))
  for step in range(0,total_distance,walk_speed):
      frames.append({'angle': target_angle, 'position': Point(p_src.x + math.cos(target_angle) * step,p_src.y + math.sin(target_angle)* step)})
  frames.append({'angle': target_angle, 'position':p_dst})
  return frames