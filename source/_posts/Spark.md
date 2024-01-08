---
title: Spark
date: 2023-05-14 16:49:33
tags: ['chatGPT']
---
from pyspark import SparkConf, SparkContext
import os

配置 PySpark
conf = SparkConf().setAppName("WeatherDataProcessing")
sc = SparkContext(conf=conf)

从 HDFS 读取 station.txt 文件
station = sc.textFile("hdfs://localhost:9000/user/data/input/station.txt").map(int).collect()

dir_path = 'hdfs://localhost:9000/user/data/input/data/'
start_y = 1980
end_y = 2020

def process_data(line, prefix):
line = line.split()
station_id = int(line[0])
if station_id in station:
return (station_id, {prefix: line[1:]})
else:
return None

def save_data_to_hdfs(rdd, prefix, station_id, year):
local_path = f"./RESULTS_py/{prefix}{station_id}{year}.txt"
os.makedirs(os.path.dirname(local_path), exist_ok=True)
rdd.saveAsTextFile(local_path)
hdfs_path = f"hdfs://localhost:9000/user/data/output/{prefix}{station_id}{year}.txt"
rdd.saveAsTextFile(hdfs_path)

for y in range(start_y, end_y):
print(y)

scheme
Copy
# 初始化一个空的累积 RDD 字典，用于存储每个站点每个前缀类型的数据
accumulated_data = {(station_id, prefix): sc.emptyRDD() for station_id in station for prefix in ['PRS', 'TEM', 'RHU', 'WIN', 'EVP', 'GST', 'PRE', 'SSD']}

for m in range(1, 13):
    print(m)
    yyyymm = f"{y}{m:02d}"

    for prefix, code in [('PRS', '10004'), ('TEM', '12001'), ('RHU', '13003'), ('WIN', '11002'), ('EVP', '13240'), ('GST', '12030-0cm'), ('PRE', '13011'), ('SSD', '14032')]:
        filename = os.path.join(dir_path, f"SURF_CLI_CHN_MUL_DAY-{prefix}-{code}-{yyyymm}.TXT")
        rdd = sc.textFile(filename)\
                .map(lambda line: process_data(line, prefix))\
                .filter(lambda x: x is not None)\
                .reduceByKey(lambda a, b: {**a, **b})

        # 将每个月的数据整合到累积 RDD 中
        for station_id in station:
            station_rdd = rdd.filter(lambda x: x[0] == station_id).map(lambda x: x[1][prefix])
            accumulated_data[(station_id, prefix)] = accumulated_data[(station_id, prefix)].union(station_rdd)

# 保存累积的 RDD 到 HDFS
for station_id, prefix in accumulated_data.keys():
    save_data_to_hdfs(accumulated_data[(station_id, prefix)], prefix, station_id, y)
sc.stop()这段代码的含义解释一下，然后输出出来的文件是什么东西也解释一下

这段代码是一个 PySpark 脚本，用于处理中国气象局公布的气象数据。代码的主要功能是将指定时间段内的气象数据整合到一个大的 RDD 中，并将其保存到 HDFS 中。

具体地，代码首先读取 HDFS 中的 station.txt 文件，该文件包含了所有站点的 ID。然后，代码遍历指定时间段内的所有月份，对于每个月份，代码会遍历所有气象数据类型（如气压、温度、湿度等），根据数据文件名和站点 ID，从 HDFS 中读取对应的数据文件，并将该文件中包含指定站点 ID 的数据提取出来，整合到一个大的 RDD 中。最后，代码将整合后的 RDD 写入到 HDFS 中。

输出的文件是每个站点每个数据类型在每个年份下的数据文件，文件名格式为 {数据类型}_{站点ID}_{年份}.txt。文件的内容是一个 RDD 中的元素，每个元素是一个字符串，表示该站点在该年份下的该数据类型的所有数据，每个数据之间用逗号分隔。

需要注意的是，代码中的 sc.textFile 函数读取的是 HDFS 中的文件，而不是本地文件系统中的文件。此外，代码中的 os.makedirs 函数也只会在本地文件系统中创建目录，而不会在 HDFS 中创建目录。如果要在 HDFS 中创建目录，需要使用 Hadoop 的命令行工具（如 hdfs dfs -mkdir）。

处理出来的txt，为什么是一个文件夹，里面的part-00000-part000021是啥东西

处理出来的 txt 文件实际上是一个文件夹，这个文件夹中包含了多个文件，每个文件的文件名以 part- 开头，后面跟着一个数字，表示该文件是整个 RDD 中的一部分。例如，part-00000 表示 RDD 中的第一个分区，part-00001 表示 RDD 中的第二个分区，以此类推。

在 Spark 中，RDD 是被划分成多个分区的，每个分区都是一个独立的数据集，可以在集群中的不同节点上进行处理。因此，Spark 将 RDD 中的每个分区保存为一个文件，这些文件位于同一个文件夹中，这样就可以在集群中不同节点上对这些分区进行处理，提高了并行处理的效率。

如果要将这些分区合并成一个文件，可以使用 Hadoop 的 hadoop fs -getmerge 命令，将这些分区下载到本地文件系统中，然后使用 cat 命令将它们合并为一个文件。

有几个part是谁来定的呢，我这里每个txt文件夹里有00-23这么多个part，对了我采用的是local[*]资源分配模式

分区数是在创建 RDD 时根据数据量和集群资源等情况自动确定的，可以使用 getNumPartitions() 方法查看 RDD 的分区数，例如：rdd.getNumPartitions()。在 PySpark 中，如果没有手动指定分区数，Spark 会根据集群中可用的 CPU 核心数来自动确定分区数。

在你的情况下，由于你使用的是 local[*] 资源分配模式，Spark 会自动将分区数设置为可用的 CPU 核心数。对于每个分区，Spark 会生成一个 part- 文件，文件名后面的数字表示该分区的编号，例如 part-00000 表示第一个分区，part-00001 表示第二个分区，以此类推。

如果需要手动指定分区数，可以使用 repartition() 或 coalesce() 方法，例如：rdd.repartition(8)，将 RDD 的分区数设置为 8。

如果是配置到多个服务器上，那么就是每个分区放在一个服务器运行吗

在 Spark 集群中，每个节点都会分配一定的资源来运行任务。当一个 RDD 被创建时，Spark 会将其划分成多个分区，并将这些分区分配到不同的节点上进行处理。每个节点会独立地处理自己分配到的分区，并将处理结果返回给驱动程序。

分区的分配是根据 Spark 的默认策略自动进行的。默认情况下，Spark 会采用哈希分区（Hash Partitioning）策略，将数据根据哈希值分配到不同的分区中。如果某个节点的资源不足以处理该分区，则该分区会被分配到其他节点上进行处理。因此，分区并不是严格地分配到单个节点上运行的。

如果你将 Spark 集群部署在多个服务器上，每个节点都可以运行一个或多个 Spark 执行器（Spark Executor），执行器会在节点上启动一个或多个线程来处理分配给它的任务。每个分区会被分配到一个执行器上进行处理，而不是一个服务器。如果某个节点上有多个执行器，则分区可能会被分配到其中的任意一个执行器上进行处理。

一个服务器对应着一个节点吗

在 Spark 集群中，一个节点通常对应着一台物理服务器或虚拟机。在每个节点上，可以运行一个或多个 Spark 执行器（Spark Executor），每个执行器会启动一个或多个处理线程来执行 Spark 任务。因此，每个节点可以同时处理多个 Spark 任务，并且会将这些任务分配到自己的执行器上进行处理。

在 Spark 中，节点的主机名和端口号可以用来标识一个节点。当 Spark 应用程序运行时，每个节点都会在其终端输出日志中打印出自己的主机名和端口号，可以使用这些信息来识别不同的节点。

需要注意的是，如果在一个物理服务器上运行了多个虚拟机（或 Docker 容器），每个虚拟机（或容器）可能对应着一个节点。在这种情况下，每个节点可能会与其他节点共享物理服务器的资源，例如 CPU、内存、网络带宽等。

wait，那就是说一个文件被分成多少个分区是根据哈希分区策略进行分区的，而一个worknode就是一个节点，也就是一个服务器或者虚拟机，然后一个worknode可以运行多个executor，一个executor可以处理一个分区，我输窦娥对吗

是的，你的理解是正确的。

在 Spark 中，数据的分区是根据哈希分区策略进行分区的，每个分区都被分配给一个执行器进行处理。在 Spark 集群中，每个节点通常对应着一台物理服务器或虚拟机，每个节点可以运行一个或多个 Spark 执行器。每个执行器可以处理一个或多个分区，具体取决于集群的资源配置和任务的负载情况。

需要注意的是，每个分区的大小（即分区中包含的数据量）不一定相同。在 Spark 中，分区的大小会根据数据的大小和分区数自动调整，以确保每个执行器都能够充分利用集群资源，并尽可能快地完成处理任务。因此，一个分区可能包含很多数据，也可能只包含少量数据，具体取决于数据的分布和集群的资源配置。

好的，谢谢你，现在麻烦你帮我写个代码，
将下面这段代码的逻辑
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

class DataProcessor:
def init(self, station_id, year_range, input_directory, output_directory):
self.station_id = station_id
self.year_range = year_range
self.input_directory = input_directory
self.output_directory = output_directory
os.makedirs(self.output_directory, exist_ok=True)

python
Copy
def load_and_extend_data(self, data_type):
    data_list = []
    for year in self.year_range:
        filename = os.path.join(self.input_directory, f"{data_type}_{self.station_id}_{year}.txt")
        data = np.genfromtxt(filename, skip_header=0)
        data_list.extend(data)
    return data_list

def process_and_save_data(self, data_types):
    data_dict = defaultdict(list)

    for data_type in data_types:
        data_dict[data_type] = self.load_and_extend_data(data_type)
        self.save_data(data_type, data_dict[data_type])

def save_data(self, data_type, data):
    np.savetxt(os.path.join(self.output_directory, f"{data_type}_{self.station_id}.txt"), data, fmt='%d')
def process_station(i):
year_range = range(1980, 2020)
data_types = ["PRS", "TEM", "RHU", "WIN", "EVP", "GST", "PRE", "SSD"]

Copy
input_directory = "./RESULTS_py/"
output_directory = "./RESULTS2_py/"

data_processor = DataProcessor(int(i), year_range, input_directory, output_directory)
data_processor.process_and_save_data(data_types)
def main():
# Load station data
station = np.loadtxt("station.txt")

Copy
with ThreadPoolExecutor() as executor:
    executor.map(process_station, station)
if name == "main":
main()

按照以下spark编写的风格
from pyspark import SparkConf, SparkContext
import os

配置 PySpark
conf = SparkConf().setAppName("WeatherDataProcessing")
sc = SparkContext(conf=conf)

从 HDFS 读取 station.txt 文件
station = sc.textFile("hdfs://localhost:9000/user/data/input/station.txt").map(int).collect()

dir_path = 'hdfs://localhost:9000/user/data/input/data/'
start_y = 1980
end_y = 2020

def process_data(line, prefix):
line = line.split()
station_id = int(line[0])
if station_id in station:
return (station_id, {prefix: line[1:]})
else:
return None

def save_data_to_hdfs(rdd, prefix, station_id, year):

Copy
hdfs_path = f"hdfs://localhost:9000/user/data/output/{prefix}_{station_id}_{year}.txt"
rdd.saveAsTextFile(hdfs_path)
for y in range(start_y, end_y):
print(y)

scheme
Copy
# 初始化一个空的累积 RDD 字典，用于存储每个站点每个前缀类型的数据
accumulated_data = {(station_id, prefix): sc.emptyRDD() for station_id in station for prefix in ['PRS', 'TEM', 'RHU', 'WIN', 'EVP', 'GST', 'PRE', 'SSD']}

for m in range(1, 13):
    print(m)
    yyyymm = f"{y}{m:02d}"

    for prefix, code in [('PRS', '10004'), ('TEM', '12001'), ('RHU', '13003'), ('WIN', '11002'), ('EVP', '13240'), ('GST', '12030-0cm'), ('PRE', '13011'), ('SSD', '14032')]:
        filename = os.path.join(dir_path, f"SURF_CLI_CHN_MUL_DAY-{prefix}-{code}-{yyyymm}.TXT")
        rdd = sc.textFile(filename)\
                .map(lambda line: process_data(line, prefix))\
                .filter(lambda x: x is not None)\
                .reduceByKey(lambda a, b: {**a, **b})

        # 将每个月的数据整合到累积 RDD 中
        for station_id in station:
            station_rdd = rdd.filter(lambda x: x[0] == station_id).map(lambda x: x[1][prefix])
            accumulated_data[(station_id, prefix)] = accumulated_data[(station_id, prefix)].union(station_rdd)

# 保存累积的 RDD 到 HDFS
for station_id, prefix in accumulated_data.keys():
    save_data_to_hdfs(accumulated_data[(station_id, prefix)], prefix, station_id, y)
sc.stop()
给我写一个整合的代码

以下是整合后的代码：

python
Copy
from pyspark import SparkConf, SparkContext
import os
import numpy as np
from collections import defaultdict

# 配置 PySpark
conf = SparkConf().setAppName("WeatherDataProcessing")
sc = SparkContext(conf=conf)

# 从 HDFS 读取 station.txt 文件
station = sc.textFile("hdfs://localhost:9000/user/data/input/station.txt").map(int).collect()

dir_path = 'hdfs://localhost:9000/user/data/input/data/'
start_y = 1980
end_y = 2020

class DataProcessor:
    def __init__(self, station_id, year_range, prefix):
        self.station_id = station_id
        self.year_range = year_range
        self.prefix = prefix

    def load_and_extend_data(self, yyyymm):
        data_list = []
        for year in self.year_range:
            filename = os.path.join(dir_path, f"SURF_CLI_CHN_MUL_DAY-{self.prefix}-{self.code}-{yyyymm}.TXT")
            data = sc.textFile(filename)\
                     .map(lambda line: self.process_data(line))\
                     .filter(lambda x: x is not None)\
                     .reduce(lambda a, b: {**a, **b})
            data_list.extend(data[self.prefix])
        return data_list

    def process_data(self, line):
        line = line.split()
        station_id = int(line[0])
        if station_id == self.station_id:
            return {self.prefix: line[1:]}
        else:
            return None

    def process_and_save_data(self, y):
        data_list = self.load_and_extend_data(f"{y:04d}{self.month:02d}")
        self.save_data(data_list)

    def save_data(self, data):
        rdd = sc.parallelize(data)
        hdfs_path = f"hdfs://localhost:9000/user/data/output/{self.prefix}_{self.station_id}_{self.year}.txt"
        rdd.saveAsTextFile(hdfs_path)

for y in range(start_y, end_y):
    for m in range(1, 13):
        year = y
        month = m
        print(f"Processing data for {year}-{month:02d}")

        # 处理每个前缀类型的数据
        for prefix, code in [('PRS', '10004'), ('TEM', '12001'), ('RHU', '13003'), ('WIN', '11002'), ('EVP', '13240'), ('GST', '12030-0cm'), ('PRE', '13011'), ('SSD', '14032')]:
            data_processor = DataProcessor(station[0], range(year, year+1), prefix)
            data_processor.code = code
            data_processor.month = month
            data_processor.year = year
            data_processor.process_and_save_data(year)

sc.stop()
这个代码将数据处理逻辑封装到了 DataProcessor 类中，可以通过创建对象来处理每个站点的数据。在每个对象中，我们通过调用 load_and_extend_data 方法来加载并整合每个月的数据，然后将处理结果保存到 HDFS 中。

在主程序中，我们首先遍历每个年份和月份，然后为每个前缀类型创建一个 DataProcessor 对象，并调用其 process_and_save_data 方法来处理数据并保存结果到 HDFS 中。

需要注意的是，由于 PySpark 是分布式计算框架，每个节点都可以并行处理多个任务。因此，在处理数据时，我们可以将每个月的数据并行加载和处理，并将处理结果合并到一个 RDD 中，以提高处理效率。同时，我们也可以将每个站点的数据分别保存到 HDFS 中，以避免多个节点同时写入同一个文件的竞争问题。

实际上目的就是将每个台站每种数据类型的每一年数据整合到一个文件里面，也就是按照年份整合起来，可以再简化一下代码吗

当然可以，以下是进一步简化后的代码：

python
Copy
from pyspark import SparkConf, SparkContext
import os
import numpy as np
from collections import defaultdict

# 配置 PySpark
conf = SparkConf().setAppName("WeatherDataProcessing")
sc = SparkContext(conf=conf)

# 从 HDFS 读取 station.txt 文件
station = sc.textFile("hdfs://localhost:9000/user/data/input/station.txt").map(int).collect()

dir_path = 'hdfs://localhost:9000/user/data/input/data/'
start_y = 1980
end_y = 2020

def process_data(line):
    line = line.split()
    station_id = int(line[0])
    prefix = line[1]
    year = int(line[2][:4])
    data = line[3:]
    return ((station_id, prefix, year), data)

def save_data_to_hdfs(rdd, station_id, prefix, year):
    hdfs_path = f"hdfs://localhost:9000/user/data/output/{prefix}_{station_id}_{year}.txt"
    rdd.saveAsTextFile(hdfs_path)

for y in range(start_y, end_y):
    print(f"Processing data for year {y}")

    # 初始化一个空的累积 RDD 字典，用于存储每个站点每个前缀类型的数据
    accumulated_data = defaultdict(lambda: sc.emptyRDD())

    # 处理每个前缀类型的数据
    for prefix, code in [('PRS', '10004'), ('TEM', '12001'), ('RHU', '13003'), ('WIN', '11002'), ('EVP', '13240'), ('GST', '12030-0cm'), ('PRE', '13011'), ('SSD', '14032')]:
        filename = os.path.join(dir_path, f"SURF_CLI_CHN_MUL_DAY-{prefix}-{code}-{y:04d}.TXT")
        rdd = sc.textFile(filename)\
                .map(lambda line: process_data(line))\
                .filter(lambda x: x is not None)\
                .reduceByKey(lambda a, b: a + b)\
                .map(lambda x: (x[0][0], x[0][1], x[0][2], np.array(x[1], dtype=int)))

        # 将每个前缀类型的数据整合到累积 RDD 中
        for station_id in station:
            station_rdd = rdd.filter(lambda x: x[0] == station_id).map(lambda x: (x[1], x[3]))
            accumulated_data[(station_id, prefix)] = accumulated_data[(station_id, prefix)].union(station_rdd)

    # 保存累积的 RDD 到 HDFS
    for (station_id, prefix), rdd in accumulated_data.items():
        save_data_to_hdfs(rdd, station_id, prefix, y)

sc.stop()
这个代码直接按年份循环，然后处理每个前缀类型的数据并将它们整合到一个 RDD 中。然后，我们将每个站点每种前缀类型的数据分别保存到一个 HDFS 文件中。

在数据处理过程中，我们使用了一个 defaultdict 对象来管理累积的 RDD。这个对象可以自动创建空的 RDD，以确保每个站点每种前缀类型的数据都能够被正确地整合到累积的 RDD 中。

wait，这个代码读取到的文件时txt文件夹底下的分区吗

不是，这个代码读取的文件是 dir_path 变量所指定的目录下的文件。在代码中，dir_path 的值为 'hdfs://localhost:9000/user/data/input/data/'，这意味着我们需要在 HDFS 中创建一个名为 /user/data/input/data/ 的目录，并将数据文件放在这个目录下。

在这个代码中，我们使用 os.path.join 函数来构造文件路径，这是因为 PySpark 可以读取本地文件系统中的文件，所以我们可以使用标准的 Python 文件路径来指定数据文件的位置。然后，我们使用 sc.textFile 函数来读取文件并创建一个 RDD。

需要注意的是，如果数据文件被分成了多个部分（即多个分区），则 PySpark 会自动将这些部分合并成一个 RDD。这意味着，无论数据文件是单个文件还是多个分区，我们都可以使用相同的方式来处理它们。